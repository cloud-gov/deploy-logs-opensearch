#!/usr/bin/env python

import subprocess
import json
import boto3
import os
import functools
from datetime import datetime,timedelta,timezone


s3_client = boto3.client("s3")
bucket_name= "{}".format(os.environ["BUCKET"])

now = datetime.now(timezone.utc)
fifteen_minutes_ago= now - timedelta(minutes=15)
start_time = fifteen_minutes_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

timestamp_key = "timestamp"
current_stamp_response=s3_client.get_object(Bucket=bucket_name, Key=timestamp_key)
start_time = current_stamp_response['Body'].read().strip().decode('utf-8')
cf_api = os.environ.get('CF_API_URL')
cf_user = os.environ.get('CF_USERNAME')
cf_pass = os.environ.get('CF_PASSWORD')
try:
    subprocess.run(['cf', 'api', cf_api],check=True)
    subprocess.run(['cf', 'auth',cf_user,cf_pass], check=True)
    print("logged in")
except subprocess.CalledProcessError as e:
    print(f"error during login: {e}")

def get_audit_logs(start,end):
    audit_logs=[]
    cf_json = subprocess.check_output(
        "cf curl '/v3/audit_events?created_ats[gt]=" + str(start) + "&created_ats[lt]=" + str(end) + "&order_by=created_at'",
        universal_newlines=True,
        shell=True,
    )
    pages=json.loads(cf_json)
    total_pages= pages['pagination']["total_pages"]
    for page in range(total_pages):
        result= subprocess.check_output(
        "cf curl '/v3/audit_events?created_ats[gt]=" + str(start) + "&created_ats[lt]=" + str(end) + "&order_by=created_at&page=" + str(page+1) +"'",
        universal_newlines=True,
        shell=True,
        )
        data= json.loads(result)
        result_data=data.get("resources",{})
        audit_logs.extend(result_data)
    return audit_logs

@functools.cache
def get_cf_entity_name(entity, guid):
    """
    Retrieves the name of a CF entity from a GUID.
    """
    if not guid:
        return
    cf_json = subprocess.check_output(
        "cf curl /v3/" + entity + "/" + guid,
        universal_newlines=True,
        shell=True,
    )
    cf_data = json.loads(cf_json)
    return cf_data.get("name", "N/A")


def upload_to_s3(bucket_name, object_name, data):
    try:
        body = '\n'.join([
                    json.dumps({
                           **{k: v for k,v in item.items() if k not in ["links"]},
                           "organization_name": get_cf_entity_name("organizations", f"{item['organization']['guid']}") if f"{item['organization']['guid']}" else "",
                           "space_name": get_cf_entity_name("spaces", f"{item['space']['guid']}") if  f"{item['space']['guid']}" else ""
                           })
                          for item in data
                          ])
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_name,
            Body=body,
            ContentType='application/json'
            )
        print("success for time "+ str(start_time))
    except Exception as e:
        print(e)
        print(f'Error upload file to S3 for time starting' + str(start_time))

def update_latest_stamp_in_s3(latest_timestamp):
    data = latest_timestamp
    s3_client.put_object(
            Bucket=bucket_name,
            Key=timestamp_key,
            Body=data,
            )

def main():
    try:
        audit_logs = get_audit_logs(start_time,end_time)
        timestamp=audit_logs[-1]['created_at']
        object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.minute:02d}/{now.second:02d}"
        upload_to_s3(bucket_name, object_name,audit_logs)
        # update latest timestamp on success
        update_latest_stamp_in_s3(timestamp)
    except Exception as e:
        print("error " + str(e))
        exit(1)

if __name__ == "__main__":
    main()
