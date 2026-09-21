#!/usr/bin/env python

from urllib.parse import urljoin
from botocore.exceptions import ClientError

import json
import boto3
import requests
import os
import functools
import re
from datetime import datetime, timedelta, timezone


s3_client = boto3.client("s3")
timestamp_key = "timestamp"

no_org_key_segment = "_no-org"

org_guid_pattern = re.compile(r"[A-Za-z0-9-]{1,64}")


class AuditEventsS3Uploader:
    def __init__(self):
        self.CF_API_URL = os.environ.get("CF_API_URL")
        self.UAA_API_URL = os.environ.get("UAA_API_URL")
        self.UAA_CLIENT_ID = os.environ.get("UAA_CLIENT_ID")
        self.UAA_CLIENT_SECRET = os.environ.get("UAA_CLIENT_SECRET")
        self.bucket_name = "{}".format(os.environ["BUCKET"])
        self.default_time = os.environ.get("DEFAULT_TIME")
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

    def get_audit_logs(self, start, end):
        audit_logs = []

        with requests.Session() as s:
            s.headers["Authorization"] = f"Bearer {self.token}"
            params = {
                "created_ats[gt]": str(start),
                "created_ats[lt]": str(end),
                "order_by": "created_at",
            }
            url = urljoin(self.CF_API_URL, "/v3/audit_events")

            first_response = s.get(url, params=params)
            data = first_response.json()
            audit_logs.extend(data["resources"])

            while data["pagination"]["next"] is not None:
                data = s.get(data["pagination"]["next"]["href"]).json()
                audit_logs.extend(data["resources"])

        return audit_logs

    def transform_audit_event(self, audit_event):
        transformed_event = audit_event

        # remove "links" property from event
        transformed_event.pop("links")

        if organization := audit_event.get("organization"):
            if organization_name := self.get_cf_entity_name(
                "organizations",
                organization.get("guid", None),
            ):
                transformed_event["organization_name"] = organization_name

        if space := audit_event.get("space"):
            if space_name := self.get_cf_entity_name("spaces", space.get("guid", None)):
                transformed_event["space_name"] = space_name

        return transformed_event

    def get_org_key_segment(self, audit_event):
        organization = audit_event.get("organization") or {}
        org_guid = organization.get("guid") or ""

        if not org_guid_pattern.fullmatch(org_guid):
            return no_org_key_segment

        return org_guid

    def group_audit_events_by_org(self, audit_events):
        grouped_events = {}

        for audit_event in audit_events:
            org_key_segment = self.get_org_key_segment(audit_event)
            grouped_events.setdefault(org_key_segment, []).append(audit_event)

        return grouped_events

    def build_object_name(self, now, org_key_segment):
        date_path = (
            f"{now.month:02d}/{now.day:02d}"
            f"/{now.hour:02d}/{now.minute:02d}/{now.second:02d}"
        )

        if org_key_segment == no_org_key_segment:
            return f"{no_org_key_segment}/{now.year}/{date_path}"

        return f"{now.year}/{org_key_segment}/{date_path}"

    # Upload a batch of audit events to S3 as a single object
    def put_audit_events_to_s3(self, object_name, audit_events):
        body = "\n".join(
            [
                json.dumps(self.transform_audit_event(audit_event))
                for audit_event in audit_events
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
        time_ago = now - timedelta(minutes=int(self.default_time))
        start_time = time_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
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

    def upload_audit_events_to_s3(self):
        now = datetime.now(timezone.utc)
        (start_time, end_time) = self.get_start_end_time(now)

        audit_logs = self.get_audit_logs(start_time, end_time)
        if len(audit_logs) > 0:
            timestamp = audit_logs[-1]["created_at"]
            for org_key_segment, org_audit_logs in self.group_audit_events_by_org(
                audit_logs
            ).items():
                object_name = self.build_object_name(now, org_key_segment)
                try:
                    self.put_audit_events_to_s3(object_name, org_audit_logs)
                    print(
                        f"success for org {org_key_segment} with start time "
                        f"{start_time} and end time {end_time}"
                    )
                except Exception as e:
                    print(
                        f"Error upload file to S3 for org {org_key_segment} for "
                        f"time starting {start_time} and end time {end_time}"
                    )
                    raise e

            self.update_latest_stamp_in_s3(timestamp)
        else:
            self.update_latest_stamp_in_s3(end_time)


def main():
    audit_events_s3_uploader = AuditEventsS3Uploader()
    audit_events_s3_uploader.upload_audit_events_to_s3()


if __name__ == "__main__":
    main()
