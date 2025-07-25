#!/usr/bin/env python

from urllib.parse import urljoin
from botocore.exceptions import ClientError

import json
import boto3
import requests
import os
import functools
from datetime import datetime, timedelta, timezone

# AWS clients
s3_client = boto3.client("s3")
cloudwatch_client = boto3.client("cloudwatch")
es_client = boto3.client("es")
sts = boto3.client("sts")

# needed for Arn based operations
account_id = sts.get_caller_identity()["Account"]
region = boto3.Session().region_name

timestamp_key = "timestamp"
daily_key = "daily_timestamp"
S3_PREFIX = "cg-"
DOMAIN_PREFIX = "cg-broker-"

opensearch_domain_metrics = [
    {"name": "CPUUtilization", "unit": "Percent"},
    {"name": "JVMMemoryPressure", "unit": "Percent"},
    {"name": "FreeStorageSpace", "unit": "Gigabytes"},
    {"name": "OldGenJVMMemoryPressure", "unit": "Percent"},
    {"name": "MasterCPUUtilization", "unit": "Percent"},
    {"name": "MasterJVMMemoryPressure", "unit": "Percent"},
    {"name": "MasterOldGenJVMMemoryPressure", "unit": "Percent"},
    {"name": "ThreadpoolWriteQueue", "unit": "Count"},
    {"name": "ThreadpoolSearchQueue", "unit": "Count"},
    {"name": "ThreadpoolSearchRejected", "unit": "Count"},
    {"name": "ThreadpoolWriteRejected", "unit": "Count"},
]
domain_node_exclude_list = [
    "FreeStorageSpace",
    "MasterCPUUtilization",
    "MasterJVMMemoryPressure",
    "MasterOldGenJVMMemoryPressure",
    "ThreadpoolWriteRejected",
    "ThreadpoolSearchRejected",
]
no_unit_list = ["FreeStorageSpace"]

s3_daily_metrics = [{"name": "BucketSizeBytes", "unit": "Bytes"}]


class MetricEventsS3Uploader:
    def __init__(self):
        self.bucket_name = "{}".format(os.environ["BUCKET"])
        self.environment = "{}".format(os.environ["ENVIRONMENT"])
        self.s3_prefix = (
            f"{self.environment}-{S3_PREFIX}"
            if self.environment in ["development", "staging"]
            else S3_PREFIX
        )
        if self.environment == "production":
            self.domain_prefix = DOMAIN_PREFIX + "prd-"
        if self.environment == "staging":
            self.domain_prefix = DOMAIN_PREFIX + "stg-"
        if self.environment == "development":
            self.domain_prefix = DOMAIN_PREFIX + "dev-"
        self.is_daily = False

    # some metrics need a specific instance called for them
    def get_instance_ids_for_domain(self, namespace, domain, metric):

        response = cloudwatch_client.list_metrics(
            Namespace=namespace,
            Dimensions=[{"Name": "DomainName", "Value": domain}],
            MetricName=metric["name"],
        )
        instance_ids = []
        for metric in response["Metrics"]:
            for dim in metric["Dimensions"]:
                if dim["Name"] == "NodeId":
                    instance_ids.append(dim["Value"])
        return instance_ids

    def get_metric_logs(
        self,
        start,
        end,
        namespace,
        metric,
        dimensions,
        period,
        statistic,
        tags,
        instance=None,
    ):
        unit = metric["unit"]
        if metric["name"] in no_unit_list:
            unit = None
        kwargs = {
            "Namespace": namespace,
            "MetricName": metric["name"],
            "Dimensions": dimensions,
            "StartTime": start,
            "EndTime": end,
            "Period": period,
            "Statistics": statistic,
        }
        if unit:
            kwargs["Unit"] = unit
        response = cloudwatch_client.get_metric_statistics(**kwargs)
        datapoints = response.get("Datapoints", [])

        if not datapoints:
            return []

        metric_events = []
        for dp in datapoints:
            dp["Tags"] = tags
            dp["MetricName"] = metric["name"]
            dp["InstanceName"] = instance
            dp["Time"] = dp["Timestamp"].isoformat()
            dp.pop("Timestamp", None)
            metric_events.append(dp)
        return metric_events

    def get_cg_domains(self):
        domain_list = es_client.list_domain_names()
        domain_names = [d["DomainName"] for d in domain_list["DomainNames"]]
        matching_domains = [d for d in domain_names if d.startswith(self.domain_prefix)]
        return matching_domains

    # Upload a batch of metric events to S3 as a single object
    def put_metric_events_to_s3(self, object_name, metric_events):
        body = "\n".join([json.dumps(metric_event) for metric_event in metric_events])
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_name,
            Body=body,
            ContentType="text/plain",
            ServerSideEncryption="AES256",
        )

    def update_latest_stamp_in_s3(self, latest_timestamp, key):
        data = latest_timestamp
        s3_client.put_object(
            Bucket=self.bucket_name, Key=key, Body=data, ServerSideEncryption="AES256"
        )

    def get_check_daily_time(self, now):
        try:
            current_stamp_response = s3_client.get_object(
                Bucket=self.bucket_name, Key=daily_key
            )
            start_time_str = (
                current_stamp_response["Body"].read().strip().decode("utf-8")
            )
            start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
            start_time = start_time.replace(tzinfo=timezone.utc)
        except ClientError as e:
            # There is no timestamp key yet
            if e.response["Error"]["Code"] == "NoSuchKey":
                start_time = now
                print(
                    f"No existing daily timestamp, starting from {start_time.isoformat()}"
                )
                self.is_daily = True
                return
            else:
                raise e
        if start_time < now - timedelta(hours=12):
            self.is_daily = True

    def get_start_end_time(self, now):
        end_time_aligned = now - timedelta(minutes=2)
        fifteen_minutes_ago = end_time_aligned - timedelta(minutes=15)
        start_time = fifteen_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = end_time_aligned.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            current_stamp_response = s3_client.get_object(
                Bucket=self.bucket_name, Key=timestamp_key
            )
            start_time = current_stamp_response["Body"].read().strip().decode("utf-8")

        except ClientError as e:
            # There is no timestamp key yet
            if e.response["Error"]["Code"] == "NoSuchKey":
                print(f"No existing start timestamp, starting from {start_time}")
            else:
                raise e
        return (start_time, end_time)

    # List buckets
    # Skip buckets that aren't in environment
    def get_s3_buckets(self):
        return [
            bucket["Name"]
            for bucket in s3_client.list_buckets()["Buckets"]
            if bucket["Name"].startswith(self.s3_prefix)
        ]

    def generate_s3_daily_metrics(self, now):
        buckets = self.get_s3_buckets()
        s3_bucket_logs = []

        for s3_instance in buckets:

            tags = {}
            # Retrieve all of the tags associated with the instance.
            try:
                s3_instance_tag_list = s3_client.get_bucket_tagging(Bucket=s3_instance)
                tag_list = s3_instance_tag_list.get("TagSet", [])
                tags = {tag.get("Key"): tag.get("Value") for tag in tag_list}
            except ClientError as e:
                print(e)
                print(s3_instance)
                continue
            org_guid_exists = tags.get("Organization GUID")
            if not org_guid_exists:
                print(f"Skipping {s3_instance} missing org tag")
                continue
            for metric in s3_daily_metrics:
                dimensions = [
                    {"Name": "BucketName", "Value": s3_instance},
                    {"Name": "StorageType", "Value": "StandardStorage"},
                ]
                s3_logs = self.get_metric_logs(
                    start=now - timedelta(days=1),
                    end=now,
                    namespace="AWS/S3",
                    metric=metric,
                    dimensions=dimensions,
                    period=86400,
                    statistic=["Average"],
                    tags=tags,
                )
                s3_bucket_logs.extend(s3_logs)
        return s3_bucket_logs

    def generate_opensearch_domain_metrics(self, start_time, end_time):
        domains = self.get_cg_domains()
        domain_logs = []

        for domain in domains:
            arn = f"arn:aws-us-gov:es:{region}:{account_id}:domain/{domain}"
            try:
                tag_response = es_client.list_tags(ARN=arn)
                tags = {
                    tag["Key"]: tag["Value"] for tag in tag_response.get("TagList", [])
                }
                tags["DomainName"] = domain
            except Exception as e:
                print(f"Error getting tags for {domain}: {e}")
                tags = {}

            for metric in opensearch_domain_metrics:
                if metric["name"] not in domain_node_exclude_list:
                    instance_ids = self.get_instance_ids_for_domain(
                        "AWS/ES", domain, metric
                    )
                    if instance_ids:
                        for instance in instance_ids:
                            dimensions = [
                                {"Name": "DomainName", "Value": domain},
                                {"Name": "NodeId", "Value": instance},
                                {"Name": "ClientId", "Value": str(account_id)},
                            ]
                            metric_logs = self.get_metric_logs(
                                start_time,
                                end_time,
                                namespace="AWS/ES",
                                metric=metric,
                                dimensions=dimensions,
                                period=60,
                                statistic=["Average"],
                                tags=tags,
                                instance=instance,
                            )
                            domain_logs.extend(metric_logs)
                    else:
                        dimensions = [
                            {"Name": "DomainName", "Value": domain},
                            {"Name": "ClientId", "Value": str(account_id)},
                        ]
                        metric_logs = self.get_metric_logs(
                            start_time,
                            end_time,
                            namespace="AWS/ES",
                            metric=metric,
                            dimensions=dimensions,
                            period=60,
                            statistic=["Average"],
                            tags=tags,
                        )
                        domain_logs.extend(metric_logs)
                else:
                    dimensions = [
                        {"Name": "DomainName", "Value": domain},
                        {"Name": "ClientId", "Value": str(account_id)},
                    ]
                    metric_logs = self.get_metric_logs(
                        start_time,
                        end_time,
                        namespace="AWS/ES",
                        metric=metric,
                        dimensions=dimensions,
                        period=60,
                        statistic=["Average"],
                        tags=tags,
                    )
                    domain_logs.extend(metric_logs)
        return domain_logs

    def upload_metric_events_to_s3(self):
        now = datetime.now(timezone.utc)
        (start_time, end_time) = self.get_start_end_time(now)
        self.get_check_daily_time(now)

        # Opensearch_domain logs
        domain_logs = self.generate_opensearch_domain_metrics(
            start_time=start_time, end_time=end_time
        )
        if len(domain_logs) > 0:
            timestamp = end_time
            object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.minute:02d}/{now.second:02d}"
            try:
                self.put_metric_events_to_s3(object_name, domain_logs)
                print(f"success for start time {start_time} and end time {end_time}")
            except Exception as e:
                print(
                    f"Error upload file to S3 for time starting {start_time} and end time {end_time}"
                )
                raise e
            self.update_latest_stamp_in_s3(timestamp, timestamp_key)
        else:
            self.update_latest_stamp_in_s3(end_time, timestamp_key)

        if self.is_daily:
            daily_point = self.generate_s3_daily_metrics(now=now)
            if len(daily_point) > 0:
                object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/s3_daily"
                try:
                    self.put_metric_events_to_s3(object_name, daily_point)
                    print(f"success for daily")
                    self.update_latest_stamp_in_s3(
                        now.strftime("%Y-%m-%dT%H:%M:%SZ"), daily_key
                    )
                except Exception as e:
                    print(f"Error upload file to S3 for daily")
                    raise e
            else:
                print("no daily points")


def main():
    metric_events_s3_uploader = MetricEventsS3Uploader()
    metric_events_s3_uploader.upload_metric_events_to_s3()


if __name__ == "__main__":
    main()
