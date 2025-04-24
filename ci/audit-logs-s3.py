#!/usr/bin/env python

from urllib.parse import urljoin
from botocore.exceptions import ClientError

import json
import boto3
import requests
import os
import functools
from datetime import datetime, timedelta, timezone


s3_client = boto3.client("s3")
bucket_name = "{}".format(os.environ["BUCKET"])
timestamp_key = "timestamp"

CF_API_URL = os.environ.get("CF_API_URL")
UAA_API_URL = os.environ.get("UAA_API_URL")
UAA_CLIENT_ID = os.environ.get("UAA_CLIENT_ID")
UAA_CLIENT_SECRET = os.environ.get("UAA_CLIENT_SECRET")


def get_client_credentials_token():
    response = requests.post(
        urljoin(UAA_API_URL, "oauth/token"),
        data={
            "grant_type": "client_credentials",
            "client_id": UAA_CLIENT_ID,
            "client_secret": UAA_CLIENT_SECRET,
            "response_type": "token",
        },
        auth=requests.auth.HTTPBasicAuth(UAA_CLIENT_ID, UAA_CLIENT_SECRET),
        timeout=30,
    )

    response.raise_for_status()
    return response.json()["access_token"]


def get_audit_logs(start, end):
    audit_logs = []
    token = get_client_credentials_token()
    with requests.Session() as s:
        s.headers["Authorization"] = f"Bearer {token}"
        params = {
            "created_ats[gt]": str(start),
            "created_ats[lt]": str(end),
            "order_by": "created_at",
        }
        url = urljoin(CF_API_URL, "v3/roles")

        first_response = s.get(url, params=params)
        data = first_response.json()
        audit_logs.extend(data["resources"])

        while data["pagination"]["next"] is not None:
            data = s.get(data["pagination"]["next"]["href"]).json()
            audit_logs.extend(data["resources"])

    return audit_logs


@functools.cache
def get_cf_entity_name(session, entity_path, entity_data):
    """
    Retrieves the name of a CF entity from a GUID.
    """
    if not entity_data["guid"]:
        return

    guid = entity_data["guid"]
    url = urljoin(CF_API_URL, f"v3/{entity_path}/{guid}")
    response = session.get(url)
    data = response.json()
    return data["name"]


def transform_audit_event_record(session, audit_event):
    return {
        **{k: v for k, v in audit_event.items() if k not in ["links"]},
        "organization_name": get_cf_entity_name(
            session, "organizations", audit_event["organization"]
        ),
        "space_name": get_cf_entity_name(session, "spaces", audit_event["space"]),
    }


# Upload a batch of audit events to S3 as a single object
def upload_audit_events_to_s3(bucket_name, object_name, audit_events):
    token = get_client_credentials_token()
    with requests.Session() as s:
        s.headers["Authorization"] = f"Bearer {token}"
        body = "\n".join(
            [
                json.dumps(transform_audit_event_record(s, audit_event))
                for audit_event in audit_events
            ]
        )
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=body,
        ContentType="application/json",
    )


def update_latest_stamp_in_s3(latest_timestamp):
    data = latest_timestamp
    s3_client.put_object(
        Bucket=bucket_name,
        Key=timestamp_key,
        Body=data,
    )


def get_start_end_time(now):
    fifteen_minutes_ago = now - timedelta(minutes=15)
    start_time = fifteen_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        current_stamp_response = s3_client.get_object(
            Bucket=bucket_name, Key=timestamp_key
        )
        start_time = current_stamp_response["Body"].read().strip().decode("utf-8")

    except ClientError as e:
        # There is no timestamp key yet
        if e.response["Error"]["Code"] == "NoSuchKey":
            print(f"No existing start timestamp, starting from {start_time}")
        else:
            raise e
    return (start_time, end_time)


def upload_audit_logs_to_s3():
    now = datetime.now(timezone.utc)
    (start_time, end_time) = get_start_end_time(now)

    audit_logs = get_audit_logs(start_time, end_time)
    if len(audit_logs) > 0:
        timestamp = audit_logs[-1]["created_at"]
        object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.minute:02d}/{now.second:02d}"
        try:
            upload_audit_events_to_s3(bucket_name, object_name, audit_logs)
            print(f"success for start time {start_time} and end time {end_time}")
        except Exception as e:
            print(
                f"Error upload file to S3 for time starting {start_time} and end time {end_time}"
            )
            raise e
        update_latest_stamp_in_s3(timestamp)
    else:
        update_latest_stamp_in_s3(end_time)


def main():
    upload_audit_logs_to_s3()


if __name__ == "__main__":
    main()