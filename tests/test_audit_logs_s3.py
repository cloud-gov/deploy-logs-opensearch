import pytest
import uuid
import requests_mock
import json

from datetime import datetime
from ci.upload_audit_events_s3 import AuditEventsS3Uploader


@pytest.fixture
def audit_event():
    return {
        "guid": str(uuid.uuid4()),
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "audit.service_instance.show",
        "actor": {"guid": str(uuid.uuid4()), "type": "user", "name": "fake-user"},
        "target": {
            "guid": str(uuid.uuid4()),
            "type": "service_instance",
            "name": "fake-service",
        },
        "data": {"request": None},
        "space": {"guid": str(uuid.uuid4())},
        "organization": {"guid": str(uuid.uuid4())},
        "links": {"self": {"href": "fake-url"}},
    }


def test_transform_audit_event_record(audit_event):
    with requests_mock.Mocker(real_http=False) as m:
        m.post(
            "http://uaa.localhost/oauth/token",
            text=json.dumps(dict(access_token="fake-token")),
        )

        org_guid = audit_event["organization"]["guid"]
        m.get(
            f"http://cf.localhost/v3/organizations/{org_guid}",
            text=json.dumps(dict(name="fake-org")),
        )

        space_guid = audit_event["space"]["guid"]
        m.get(
            f"http://cf.localhost/v3/spaces/{space_guid}",
            text=json.dumps(dict(name="fake-space")),
        )

        audit_events_s3_uploader = AuditEventsS3Uploader()
        transformed_record = audit_events_s3_uploader.transform_audit_event(audit_event)

        assert transformed_record == {
            "guid": audit_event["guid"],
            "created_at": audit_event["created_at"],
            "updated_at": audit_event["updated_at"],
            "type": audit_event["type"],
            "actor": audit_event["actor"],
            "target": audit_event["target"],
            "data": audit_event["data"],
            "space": audit_event["space"],
            "organization": audit_event["organization"],
            "organization_name": "fake-org",
            "space_name": "fake-space",
        }
