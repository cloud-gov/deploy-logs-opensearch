import pytest
import uuid
import requests_mock
import json

from datetime import datetime, timezone
from unittest.mock import patch
from ci.upload_audit_events_s3_org_keyed import (
    AuditEventsS3Uploader,
    no_org_key_segment,
    no_space_key_segment,
    org_events_key_segment,
    orgs_key_prefix,
)


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


@pytest.fixture
def fake_requests(audit_event):
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
        yield m


def test_transform_audit_event(fake_requests, audit_event):
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


def test_transform_audit_event_no_space(fake_requests, audit_event):
    audit_event["space"] = None

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
    }

    assert len(fake_requests.request_history) == 2
    org_guid = audit_event["organization"]["guid"]
    assert fake_requests.request_history[1].path == f"/v3/organizations/{org_guid}"


def test_transform_audit_event_no_organization(fake_requests, audit_event):
    audit_event["organization"] = None

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
        "space_name": "fake-space",
    }

    assert len(fake_requests.request_history) == 2
    space_guid = audit_event["space"]["guid"]
    assert fake_requests.request_history[1].path == f"/v3/spaces/{space_guid}"


def test_transform_audit_event_organization_does_not_exist(fake_requests, audit_event):
    org_guid = audit_event["organization"]["guid"]
    fake_requests.get(
        f"http://cf.localhost/v3/organizations/{org_guid}",
        status_code=404,
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
        "space_name": "fake-space",
    }

    assert len(fake_requests.request_history) == 3


def test_transform_audit_event_space_does_not_exist(fake_requests, audit_event):
    space_guid = audit_event["space"]["guid"]
    fake_requests.get(
        f"http://cf.localhost/v3/spaces/{space_guid}",
        status_code=404,
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
    }

    assert len(fake_requests.request_history) == 3


#
# Organization and space keyed S3 object names
#


def make_audit_event(organization=None, space=None, created_at=None):
    """
    Builds a minimal audit event. "links" is always present because
    transform_audit_event pops it unconditionally.
    """
    return {
        "guid": str(uuid.uuid4()),
        "created_at": created_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "audit.app.update",
        "data": {"request": None},
        "space": space,
        "organization": organization,
        "links": {"self": {"href": "fake-url"}},
    }


def test_get_key_segments_uses_organization_and_space_guids(fake_requests):
    org_guid = str(uuid.uuid4())
    space_guid = str(uuid.uuid4())
    audit_event = make_audit_event(
        organization={"guid": org_guid}, space={"guid": space_guid}
    )

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.get_key_segments(audit_event) == (
        org_guid,
        space_guid,
    )


@pytest.mark.parametrize(
    "entity",
    [
        None,
        {},
        {"guid": None},
        {"guid": ""},
    ],
    ids=["no-entity", "empty-entity", "null-guid", "empty-guid"],
)
def test_get_key_segments_falls_back_to_placeholders(fake_requests, entity):
    audit_event = make_audit_event(organization=entity, space=entity)

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.get_key_segments(audit_event) == (
        no_org_key_segment,
        no_space_key_segment,
    )


def test_get_key_segments_keys_org_level_events_under_the_org(fake_requests):
    """
    An event with an organization but no space is an org level event, so it is
    keyed under the org rather than under a space placeholder.
    """
    org_guid = str(uuid.uuid4())

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.get_key_segments(
        make_audit_event(organization={"guid": org_guid}, space=None)
    ) == (org_guid, org_events_key_segment)


def test_get_key_segments_falls_back_per_entity(fake_requests):
    """
    A missing space must not drag the organization segment to the placeholder,
    and vice versa.
    """
    org_guid = str(uuid.uuid4())
    space_guid = str(uuid.uuid4())

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.get_key_segments(
        make_audit_event(organization={"guid": org_guid}, space=None)
    ) == (org_guid, org_events_key_segment)

    assert audit_events_s3_uploader.get_key_segments(
        make_audit_event(organization=None, space={"guid": space_guid})
    ) == (no_org_key_segment, space_guid)


@pytest.mark.parametrize(
    "guid",
    [
        "../../etc/passwd",
        "some/nested/guid",
        "..",
        "timestamp/../timestamp",
        "guid with spaces",
        "a" * 65,
        no_org_key_segment,
        no_space_key_segment,
        org_events_key_segment,
    ],
    ids=[
        "traversal",
        "separators",
        "parent-ref",
        "watermark-overwrite",
        "whitespace",
        "over-length",
        "impersonates-no-org",
        "impersonates-no-space",
        "impersonates-org-events",
    ],
)
def test_get_key_segments_rejects_unsafe_guid(fake_requests, guid):
    """
    The GUIDs come from the CF API and are interpolated into an S3 key, so
    anything that could rewrite the key path must be rejected rather than
    passed through.
    """
    audit_event = make_audit_event(organization={"guid": guid}, space={"guid": guid})

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.get_key_segments(audit_event) == (
        no_org_key_segment,
        no_space_key_segment,
    )


def test_build_object_name_nests_space_under_org(fake_requests):
    now = datetime(2026, 9, 18, 14, 30, 5, tzinfo=timezone.utc)

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert (
        audit_events_s3_uploader.build_object_name(
            now, ("fake-org-guid", "fake-space-guid")
        )
        == "orgs/fake-org-guid/fake-space-guid/2026/09/18/14/30/05"
    )


def test_build_object_name_keeps_placeholders_under_orgs_prefix(fake_requests):
    """
    Org-less and space-less events stay under the same orgs/ prefix so a single
    prefix covers every audit object.
    """
    now = datetime(2026, 9, 18, 14, 30, 5, tzinfo=timezone.utc)

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert audit_events_s3_uploader.build_object_name(
        now, (no_org_key_segment, no_space_key_segment)
    ) == (
        f"{orgs_key_prefix}/{no_org_key_segment}/{no_space_key_segment}"
        "/2026/09/18/14/30/05"
    )

    assert audit_events_s3_uploader.build_object_name(
        now, ("fake-org-guid", org_events_key_segment)
    ) == (
        f"{orgs_key_prefix}/fake-org-guid/{org_events_key_segment}/2026/09/18/14/30/05"
    )


def test_build_object_name_zero_pads_time_segments(fake_requests):
    now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    audit_events_s3_uploader = AuditEventsS3Uploader()

    assert (
        audit_events_s3_uploader.build_object_name(
            now, ("fake-org-guid", "fake-space-guid")
        )
        == "orgs/fake-org-guid/fake-space-guid/2026/01/02/03/04/05"
    )
    assert audit_events_s3_uploader.build_object_name(
        now, (no_org_key_segment, no_space_key_segment)
    ) == (
        f"{orgs_key_prefix}/{no_org_key_segment}/{no_space_key_segment}"
        "/2026/01/02/03/04/05"
    )


def test_group_audit_events_by_org_and_space(fake_requests):
    org_a_guid = str(uuid.uuid4())
    org_b_guid = str(uuid.uuid4())
    space_a_guid = str(uuid.uuid4())
    space_b_guid = str(uuid.uuid4())

    space_a_first = make_audit_event(
        organization={"guid": org_a_guid}, space={"guid": space_a_guid}
    )
    org_b_first = make_audit_event(
        organization={"guid": org_b_guid}, space={"guid": space_b_guid}
    )
    # Same org, different space: must not share an object with space_a.
    space_b_in_org_a = make_audit_event(
        organization={"guid": org_a_guid}, space={"guid": space_b_guid}
    )
    space_a_second = make_audit_event(
        organization={"guid": org_a_guid}, space={"guid": space_a_guid}
    )
    org_level_event = make_audit_event(organization={"guid": org_a_guid}, space=None)
    platform_event = make_audit_event(organization=None, space=None)

    audit_events_s3_uploader = AuditEventsS3Uploader()
    grouped_events = audit_events_s3_uploader.group_audit_events_by_org_and_space(
        [
            space_a_first,
            org_b_first,
            space_b_in_org_a,
            space_a_second,
            org_level_event,
            platform_event,
        ]
    )

    assert grouped_events == {
        (org_a_guid, space_a_guid): [space_a_first, space_a_second],
        (org_b_guid, space_b_guid): [org_b_first],
        (org_a_guid, space_b_guid): [space_b_in_org_a],
        (org_a_guid, org_events_key_segment): [org_level_event],
        (no_org_key_segment, no_space_key_segment): [platform_event],
    }
    # Per group batches must stay in the created_at order the CF API returned.
    assert grouped_events[(org_a_guid, space_a_guid)] == [space_a_first, space_a_second]


#
# upload_audit_events_to_s3: one object per organization and space
#


@pytest.fixture
def frozen_now():
    return datetime(2026, 9, 18, 14, 30, 5, tzinfo=timezone.utc)


def build_uploader(fake_requests, audit_logs, frozen_now):
    """
    Runs the uploader with the CF fetch, the time window and the S3 writes
    stubbed, so a run can be asserted against without touching S3. Returns the
    put and watermark mocks, which retain their call history after the patches
    are undone.
    """
    audit_events_s3_uploader = AuditEventsS3Uploader()

    with (
        patch.object(
            audit_events_s3_uploader, "get_audit_logs", return_value=audit_logs
        ),
        patch.object(
            audit_events_s3_uploader,
            "get_start_end_time",
            return_value=("2026-09-18T14:20:05Z", "2026-09-18T14:30:05Z"),
        ),
        patch.object(audit_events_s3_uploader, "put_audit_events_to_s3") as put_mock,
        patch.object(
            audit_events_s3_uploader, "update_latest_stamp_in_s3"
        ) as stamp_mock,
        patch("ci.upload_audit_events_s3_org_keyed.datetime") as clock_mock,
    ):
        clock_mock.now.return_value = frozen_now
        audit_events_s3_uploader.upload_audit_events_to_s3()

    return (put_mock, stamp_mock)


def test_upload_writes_one_object_per_org_and_space(fake_requests, frozen_now):
    org_a_guid = str(uuid.uuid4())
    org_b_guid = str(uuid.uuid4())
    space_a_guid = str(uuid.uuid4())
    space_b_guid = str(uuid.uuid4())

    space_a_first = make_audit_event(
        organization={"guid": org_a_guid},
        space={"guid": space_a_guid},
        created_at="2026-09-18T14:21:00Z",
    )
    org_b_first = make_audit_event(
        organization={"guid": org_b_guid},
        space={"guid": space_b_guid},
        created_at="2026-09-18T14:22:00Z",
    )
    space_a_second = make_audit_event(
        organization={"guid": org_a_guid},
        space={"guid": space_a_guid},
        created_at="2026-09-18T14:23:00Z",
    )
    org_level_event = make_audit_event(
        organization={"guid": org_a_guid},
        space=None,
        created_at="2026-09-18T14:24:00Z",
    )
    platform_event = make_audit_event(
        organization=None, space=None, created_at="2026-09-18T14:25:00Z"
    )

    (put_mock, stamp_mock) = build_uploader(
        fake_requests,
        [
            space_a_first,
            org_b_first,
            space_a_second,
            org_level_event,
            platform_event,
        ],
        frozen_now,
    )

    date_path = "2026/09/18/14/30/05"
    no_org_no_space_key = (
        f"{orgs_key_prefix}/{no_org_key_segment}/{no_space_key_segment}/{date_path}"
    )
    assert [call.args for call in put_mock.call_args_list] == [
        (
            f"{orgs_key_prefix}/{org_a_guid}/{space_a_guid}/{date_path}",
            [space_a_first, space_a_second],
        ),
        (
            f"{orgs_key_prefix}/{org_b_guid}/{space_b_guid}/{date_path}",
            [org_b_first],
        ),
        (
            f"{orgs_key_prefix}/{org_a_guid}/{org_events_key_segment}/{date_path}",
            [org_level_event],
        ),
        (no_org_no_space_key, [platform_event]),
    ]

    # Watermark is the newest created_at across all groups, not the last one's.
    stamp_mock.assert_called_once_with("2026-09-18T14:25:00Z")


def test_upload_advances_watermark_to_window_end_when_no_events(
    fake_requests, frozen_now
):
    (put_mock, stamp_mock) = build_uploader(fake_requests, [], frozen_now)

    put_mock.assert_not_called()
    stamp_mock.assert_called_once_with("2026-09-18T14:30:05Z")


def test_upload_does_not_advance_watermark_when_a_put_fails(fake_requests, frozen_now):
    """
    Fail closed: a failed upload must leave the watermark untouched so the
    window is retried rather than silently skipped.
    """
    audit_logs = [
        make_audit_event(organization={"guid": str(uuid.uuid4())}),
        make_audit_event(organization={"guid": str(uuid.uuid4())}),
    ]

    audit_events_s3_uploader = AuditEventsS3Uploader()

    with (
        patch.object(
            audit_events_s3_uploader, "get_audit_logs", return_value=audit_logs
        ),
        patch.object(
            audit_events_s3_uploader,
            "get_start_end_time",
            return_value=("2026-09-18T14:20:05Z", "2026-09-18T14:30:05Z"),
        ),
        patch.object(
            audit_events_s3_uploader,
            "put_audit_events_to_s3",
            side_effect=RuntimeError("s3 unavailable"),
        ) as put_mock,
        patch.object(
            audit_events_s3_uploader, "update_latest_stamp_in_s3"
        ) as stamp_mock,
        patch("ci.upload_audit_events_s3_org_keyed.datetime") as clock_mock,
    ):
        clock_mock.now.return_value = frozen_now

        with pytest.raises(RuntimeError, match="s3 unavailable"):
            audit_events_s3_uploader.upload_audit_events_to_s3()

    # Stops on the first failure instead of continuing through later orgs.
    assert put_mock.call_count == 1
    stamp_mock.assert_not_called()


#
# Contract between the two scripts
#


def test_shared_script_key_is_unchanged(fake_requests, frozen_now):
    """
    Guards the reason this fork exists: the staging and production script must
    keep writing one time-only object per run. If this fails, the org and space
    keyed layout has leaked into staging and production.
    """
    import ci.upload_audit_events_s3 as shared

    audit_logs = [
        make_audit_event(
            organization={"guid": str(uuid.uuid4())},
            space={"guid": str(uuid.uuid4())},
            created_at="2026-09-18T14:21:00Z",
        ),
        make_audit_event(
            organization=None, space=None, created_at="2026-09-18T14:22:00Z"
        ),
    ]

    shared_uploader = shared.AuditEventsS3Uploader()

    with (
        patch.object(shared_uploader, "get_audit_logs", return_value=audit_logs),
        patch.object(
            shared_uploader,
            "get_start_end_time",
            return_value=("2026-09-18T14:20:05Z", "2026-09-18T14:30:05Z"),
        ),
        patch.object(shared_uploader, "put_audit_events_to_s3") as put_mock,
        patch.object(shared_uploader, "update_latest_stamp_in_s3"),
        patch("ci.upload_audit_events_s3.datetime") as clock_mock,
    ):
        clock_mock.now.return_value = frozen_now
        shared_uploader.upload_audit_events_to_s3()

    # One object per run, no organization or space segment, everything in the
    # same object.
    put_mock.assert_called_once_with("2026/09/18/14/30/05", audit_logs)


def test_shared_script_has_no_org_keying_helpers(fake_requests):
    """
    The org and space keying helpers must exist only in the development fork.
    """
    import ci.upload_audit_events_s3 as shared

    assert not hasattr(shared, "orgs_key_prefix")
    assert not hasattr(shared, "no_org_key_segment")
    assert not hasattr(shared, "no_space_key_segment")
    assert not hasattr(shared, "org_events_key_segment")
    assert not hasattr(shared.AuditEventsS3Uploader, "get_key_segment")
    assert not hasattr(shared.AuditEventsS3Uploader, "get_key_segments")
    assert not hasattr(shared.AuditEventsS3Uploader, "get_org_key_segment")
    assert not hasattr(shared.AuditEventsS3Uploader, "get_space_key_segment")
    assert not hasattr(
        shared.AuditEventsS3Uploader, "group_audit_events_by_org_and_space"
    )
    assert not hasattr(shared.AuditEventsS3Uploader, "build_object_name")
