#!/usr/bin/env python

import time
from playwright.sync_api import expect
from .notifications import (
    create_email_recipient_group,
    create_notifications_channel,
    delete_notifications_channel,
    delete_email_recipient_group,
    create_alert_monitor,
)
from .utils import (
    log_in,
    switch_tenants,
    open_primary_menu_link,
    click_contextual_menu_link,
)
from . import AUTH_PROXY_URL, CF_ORG_1_NAME, CF_ORG_2_NAME

test_run_timestamp = int(time.time())
test_email_recipient_group_name = f"TestEmailRecipientGroup-{test_run_timestamp}"
test_channel_name = f"TestChannel-{test_run_timestamp}"
test_monitor_name = f"TestMonitor-{test_run_timestamp}"
test_trigger_name = f"TestTrigger-{test_run_timestamp}"
test_action_name = f"TestAction-{test_run_timestamp}"


def test_user_can_create_alerts(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Email recipient groups")

    create_email_recipient_group(page, user_1, test_email_recipient_group_name)

    click_contextual_menu_link(page, "Channels")

    create_notifications_channel(
        page, test_email_recipient_group_name, test_channel_name
    )

    open_primary_menu_link(page, "Alerting")

    create_alert_monitor(
        page, test_monitor_name, test_trigger_name, test_action_name, test_channel_name
    )


def test_user_cannot_see_alert_objects(user_2, page):
    log_in(user_2, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_2_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Email recipient groups")

    page.wait_for_load_state("domcontentloaded")
    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).not_to_be_visible()


def test_user_can_delete_alerts(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Channels")

    delete_notifications_channel(page, test_channel_name)

    click_contextual_menu_link(page, "Email recipient groups")

    delete_email_recipient_group(page, test_email_recipient_group_name)
