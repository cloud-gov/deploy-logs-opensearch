#!/usr/bin/env python3

import subprocess
import json
import boto3
from datetime import datetime,timedelta,timezone


s3_client = boto3.client("s3")
bucket_name="cf-audit-s3-for-opensearch"

now = datetime.now(timezone.utc)
object_key=f"{now.year}/{now.month:02d}/{now.day:02d}/{now.minute:02d}/audit.json"
fifteen_minutes_ago= now - timedelta(minutes=15)

start_time = fifteen_minutes_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_audit_logs(start,end):
    audit_logs=[]
    cf_json = subprocess.check_output(
        "cf curl /v3/audit_events?created_ats[gt]=" + str(start) + "&created_ats[lt]=" + str(end) + "&order_by=created_at",
        universal_newlines=True,
        shell=True,
    )
    pages=json.loads(cf_json)
    total_pages= pages['pagination']["total_pages"]
    for page in range(total_pages):
        result= subprocess.check_output(
        "cf curl /v3/audit_events?created_ats[gt]=" + str(start) + "&created_ats[lt]=" + str(end) + "&order_by=created_at&page=" + str(page),
        universal_newlines=True,
        shell=True,
        )
        data= json.loads(result)
        result_data=data.get("resources",{})
        audit_logs.extend(result_data)
    return audit_logs

def main():
    audit_logs = get_audit_logs(start_time,end_time)
    try:
        s3_client.put_object(Bucket=bucket_name,Key=object_key,Body=json.dumps(audit_logs,indent=2),ContentType='application/json')
        print("success for time "+ str(start_time))
    except Exception as e:
        print(e)
        print(f'Error upload file to S3 for time starting' + str(start_time))

if __name__ == "__main__":
    main()