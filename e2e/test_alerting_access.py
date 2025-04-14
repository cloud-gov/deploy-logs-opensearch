#!/usr/bin/env python

import re
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
    click_tab_link,
)
from . import AUTH_PROXY_URL, CF_ORG_1_NAME, CF_ORG_2_NAME

test_run_timestamp = int(time.time())
test_object_prefix = "E2E-Test"
test_email_recipient_group_name = (
    f"{test_object_prefix}EmailRecipientGroup-{test_run_timestamp}"
)
test_channel_name = f"{test_object_prefix}Channel-{test_run_timestamp}"
test_monitor_name = f"{test_object_prefix}Monitor-{test_run_timestamp}"
test_trigger_name = f"{test_object_prefix}Trigger-{test_run_timestamp}"
test_action_name = f"{test_object_prefix}Action-{test_run_timestamp}"


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

    click_tab_link(page, "Monitors")

    create_alert_monitor(
        page, test_monitor_name, test_trigger_name, test_action_name, test_channel_name
    )


def test_user_cannot_see_alert_objects(user_2, page):
    log_in(user_2, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_2_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Email recipient groups")

    # Playwright discourages waiting for "networkidle". However, there is no other UI element
    # we can test to be sure that the page is finished loading. And if the page has not finished
    # loading, the assertion below checking for an element on the page may fail because the item
    # has not been loaded yet, not because it is correctly hidden from the current user.
    #
    # See https://playwright.dev/python/docs/api/class-page#page-wait-for-load-state
    page.wait_for_load_state("networkidle")
    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).not_to_be_visible()

    click_contextual_menu_link(page, "Channels")

    expect(page.locator(".euiBasicTable")).to_have_class(re.compile(r"^euiBasicTable$"))
    expect(page.get_by_text(test_channel_name, exact=True)).not_to_be_visible()

    open_primary_menu_link(page, "Alerting")

    click_tab_link(page, "Monitors")

    expect(page.get_by_text(re.compile(r"^Loading monitors\.+$"))).not_to_be_visible()
    expect(page.get_by_text(test_monitor_name, exact=True)).not_to_be_visible()


def test_user_can_delete_alerts(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Channels")

    delete_notifications_channel(page, test_channel_name)

    click_contextual_menu_link(page, "Email recipient groups")

    delete_email_recipient_group(page, test_email_recipient_group_name)
