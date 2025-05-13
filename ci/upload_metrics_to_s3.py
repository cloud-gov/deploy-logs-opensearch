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
cloudwatch_client = boto3.client('cloudwatch')
es_client = boto3.client('es')
sts = boto3.client('sts')

# needed for Arn based operations
account_id = sts.get_caller_identity()['Account']
region = boto3.Session().region_name

timestamp_key = "timestamp"
opensearch_domain_metrics = [
    {"name": "CPUUtilization", "unit": "Percent"},
    {"name": "JVMMemoryPressure", "unit": "Percent"},
    {"name": "FreeStorageSpace", "unit": "Bytes"}
]

class MetricEventsS3Uploader:
    def __init__(self):
        self.CF_API_URL = os.environ.get("CF_API_URL")
        self.UAA_API_URL = os.environ.get("UAA_API_URL")
        self.UAA_CLIENT_ID = os.environ.get("UAA_CLIENT_ID")
        self.UAA_CLIENT_SECRET = os.environ.get("UAA_CLIENT_SECRET")
        self.bucket_name = "{}".format(os.environ["BUCKET"])
        self.token = self.get_client_credentials_token()

    def get_client_credentials_token(self):
        with requests.Session() as s:
            response = s.post(
                urljoin(self.UAA_API_URL, "oauth/token"),
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.UAA_CLIENT_ID,
                    "client_secret": self.UAA_CLIENT_SECRET,
                    "response_type": "token",
                },
                auth=requests.auth.HTTPBasicAuth(
                    self.UAA_CLIENT_ID, self.UAA_CLIENT_SECRET
                ),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["access_token"]

    @functools.cache
    def get_cf_entity_name(self, entity_path, entity_guid):
        """
        Retrieves the name of a CF entity from a GUID.
        """
        if not entity_guid:
            return

        with requests.Session() as s:
            s.headers["Authorization"] = f"Bearer {self.token}"
            url = urljoin(self.CF_API_URL, f"v3/{entity_path}/{entity_guid}")
            response = s.get(url)

            if response.status_code == 404:
                return

            data = response.json()
            return data["name"]

    # some metrics need a specific instance called for them
    def get_instance_ids_for_domain(self,namespace,domain,metric):

        response = cloudwatch_client.list_metrics(
            Namespace=namespace,
            Dimensions = [{"Name": "DomainName", "Value": domain}],
            MetricName=metric["name"],

        )
        instance_ids = []
        for metric in response["Metrics"]:
            for dim in metric["Dimensions"]:
                if dim["Name"] == "NodeId":
                    instance_ids.append(dim["Value"])
        return instance_ids

    def get_metric_logs(self, start, end, namespace, metric, dimensions,period, statistic,tags,instance,org_name,space_name):
        response= cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric["name"],
            Dimensions=dimensions,
            StartTime=start,
            EndTime=end,
            Period=period,
            Statistics=statistic,
            Unit=metric["unit"]
        )
        datapoints = response.get("Datapoints",[])

        if not datapoints:
            return []

        metric_events = []
        for dp in datapoints:
            dp["Tags"] = tags
            dp["MetricName"] = metric["name"]
            dp["InstanceName"] = instance
            dp["Time"] = dp["Timestamp"].isoformat()
            dp.pop("Timestamp", None)
            dp["Organization_name"] = org_name
            dp["Space_name"] = space_name
            metric_events.append(dp)
        return metric_events


    def get_cg_domains(self):
        domain_list = es_client.list_domain_names()
        domain_names = [d['DomainName'] for d in domain_list['DomainNames']]
        matching_domains = [d for d in domain_names if d.startswith('cg-')]
        return matching_domains


    def transform_metric_event(self, metric_event):
        transformed_event = metric_event

        # remove "links" property from event
        transformed_event.pop("links")

        if organization := metric_event.get("organization"):
            if organization_name := self.get_cf_entity_name(
                "organizations",
                organization.get("guid", None),
            ):
                transformed_event["organization_name"] = organization_name

        if space := metric_event.get("space"):
            if space_name := self.get_cf_entity_name("spaces", space.get("guid", None)):
                transformed_event["space_name"] = space_name

        return transformed_event

    # Upload a batch of metric events to S3 as a single object
    def put_metric_events_to_s3(self, object_name, metric_events):
        body = "\n".join(
            [
                json.dumps(self.transform_metric_event(metric_event))
                for metric_event in metric_events
            ]
        )
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_name,
            Body=body,
            ContentType="text/plain",
            ServerSideEncryption='AES256'
        )

    def update_latest_stamp_in_s3(self, latest_timestamp):
        data = latest_timestamp
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=timestamp_key,
            Body=data,
            ServerSideEncryption='AES256'
        )

    def get_start_end_time(self, now):
        fifteen_minutes_ago = now - timedelta(minutes=15)
        start_time = fifteen_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

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

    def generate_opensearch_domain_metrics(self,start_time,end_time):
        domains = self.get_cg_domains()
        domain_logs = []

        for domain in domains:
            arn = f"arn:aws-us-gov:es:{region}:{account_id}:domain/{domain}"
            try:
                tag_response = es_client.list_tags(ARN=arn)
                tags = {tag["Key"]: tag["Value"] for tag in tag_response.get("TagList",[])}
            except Exception as e:
                print(f"Error getting tags for {domain}: {e}")
                tags = {}

            org_name = None
            space_name= None
            if organization_name := self.get_cf_entity_name(
                "organizations",
                tags.get("Organization GUID", None),
            ): org_name = organization_name
            if space_name := self.get_cf_entity_name("spaces", tags.get("Space GUID", None)): space_name = space_name

            for metric in opensearch_domain_metrics:
                instance_ids = self.get_instance_ids_for_domain("AWS/ES",domain,metric)
                if instance_ids != []:
                    for instance in instance_ids:
                        dimensions = [{"Name": "DomainName", "Value": domain},{"Name": "NodeId", "Value": instance},{"Name": "ClientId", "Value": str(account_id)}]
                        metric_logs = self.get_metric_logs(
                            start_time,
                            end_time,
                            namespace="AWS/ES",
                            metric=metric,
                            dimensions=dimensions,
                            period=60,
                            statistic=["Average"],
                            tags=tags,
                            instance=domain,
                            org_name=org_name,
                            space_name=space_name
                            )
                        domain_logs.extend(metric_logs)
                else:
                    dimensions = [{"Name": "DomainName", "Value": domain}]
                    metric_logs = self.get_metric_logs(
                        start_time,
                        end_time,
                        namespace="AWS/ES",
                        metric=metric,
                        dimensions=dimensions,
                        period=60,
                        statistic=["Average"],
                        tags=tags,
                        instance=domain,
                        org_name=org_name,
                        space_name=space_name
                        )
                    domain_logs.extend(metric_logs)
        return domain_logs


    def upload_metric_events_to_s3(self):
        now = datetime.now(timezone.utc)
        (start_time, end_time) = self.get_start_end_time(now)

        #Opensearch_domain logs
        domain_logs = self.generate_opensearch_domain_metrics(start_time=start_time,end_time=end_time)
        if len(domain_logs) > 0:
            timestamp = domain_logs[-1]["created_at"]
            object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.minute:02d}/{now.second:02d}"
            try:
                self.put_metric_events_to_s3(object_name, domain_logs)
                print(f"success for start time {start_time} and end time {end_time}")
            except Exception as e:
                print(
                    f"Error upload file to S3 for time starting {start_time} and end time {end_time}"
                )
                raise e
            self.update_latest_stamp_in_s3(timestamp)
        else:
            self.update_latest_stamp_in_s3(end_time)


def main():
    metric_events_s3_uploader = MetricEventsS3Uploader()
    metric_events_s3_uploader.upload_metric_events_to_s3()


if __name__ == "__main__":
    main()
