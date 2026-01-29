#!/usr/bin/env python

import re
import time
from playwright.sync_api import expect
from .notifications import (
    create_email_recipient_group,
    create_email_smtp_sender,
    create_notifications_channel,
    delete_notifications_channel,
    delete_email_recipient_group,
    create_alert_monitor,
    delete_alert_monitor,
    delete_email_smtp_sender,
    fill_email_recipient_group_details,
    failure_on_edit_save,
    fill_email_smtp_sender_details,
)
from .utils import (
    log_in,
    switch_tenants,
    open_primary_menu_link,
    click_contextual_menu_link,
    click_tab_link,
    wait_for_loading_finished,
    select_table_item_checkbox,
    update_rows_per_table,
    click_table_edit_button,
    click_actions_edit_link,
    click_save_button,
    dismiss_toast_notification_button,
)
from . import AUTH_PROXY_URL, CF_ORG_1_NAME, CF_ORG_2_NAME, CF_ORG_3_NAME

test_run_timestamp = int(time.time())
test_object_prefix = "E2E-Test"
test_email_recipient_group_name = (
    f"{test_object_prefix}EmailRecipientGroup-{test_run_timestamp}"
)
test_email_smtp_sender_name = (
    f"{test_object_prefix}EmailSmtpSender-{test_run_timestamp}"
).lower()
test_channel_name = f"{test_object_prefix}Channel-{test_run_timestamp}"
test_monitor_name = f"{test_object_prefix}Monitor-{test_run_timestamp}"
test_trigger_name = f"{test_object_prefix}Trigger-{test_run_timestamp}"
test_action_name = f"{test_object_prefix}Action-{test_run_timestamp}"


def test_user_can_create_alerts(user_1, page):
    def handler():
        dismiss_toast_notification_button(page)

    page.add_locator_handler(
        page.get_by_text(re.compile(r"^.*successfully created.$")),
        handler,
    )

    log_in(user_1, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Email recipient groups")

    create_email_recipient_group(page, user_1, test_email_recipient_group_name)

    click_contextual_menu_link(page, "Email senders")

    create_email_smtp_sender(page, test_email_smtp_sender_name)

    click_contextual_menu_link(page, "Channels")

    create_notifications_channel(
        page,
        test_email_recipient_group_name,
        test_email_smtp_sender_name,
        test_channel_name,
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

    wait_for_loading_finished(page)

    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).not_to_be_visible()

    click_contextual_menu_link(page, "Email senders")

    wait_for_loading_finished(page)

    expect(
        page.get_by_text(test_email_smtp_sender_name, exact=True)
    ).not_to_be_visible()

    click_contextual_menu_link(page, "Channels")

    wait_for_loading_finished(page)

    expect(page.get_by_text(test_channel_name, exact=True)).not_to_be_visible()

    open_primary_menu_link(page, "Alerting")

    click_tab_link(page, "Monitors")

    wait_for_loading_finished(page)

    expect(page.get_by_text(test_monitor_name, exact=True)).not_to_be_visible()


def test_user_can_see_but_not_edit_alert_objects(user_3, page):
    def handler():
        dismiss_toast_notification_button(page)

    page.add_locator_handler(
        page.get_by_text(re.compile(r"^There was a problem loading.*")),
        handler,
    )

    log_in(user_3, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Email recipient groups")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).to_be_visible()

    select_table_item_checkbox(page, test_email_recipient_group_name)
    click_table_edit_button(page)
    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name="Edit recipient group")).to_be_visible()

    fill_email_recipient_group_details(page, user_3, test_email_recipient_group_name)
    wait_for_loading_finished(page)
    failure_on_edit_save(page, "Failed to update recipient group")

    click_contextual_menu_link(page, "Email senders")
    wait_for_loading_finished(page)

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(page.get_by_text(test_email_smtp_sender_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, test_email_smtp_sender_name)
    click_table_edit_button(page)
    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name="Edit SMTP sender")).to_be_visible()

    fill_email_smtp_sender_details(page, test_email_smtp_sender_name)
    wait_for_loading_finished(page)
    failure_on_edit_save(page, "Failed to update sender")

    click_contextual_menu_link(page, "Channels")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    channel_link = page.get_by_role("link", name=test_channel_name, exact=True)
    expect(channel_link).to_be_visible()
    channel_link.click()

    expect(page.get_by_role("heading", name="-")).to_be_visible()

    channel_breadcrumb_link = page.get_by_role("link", name="Channels", exact=True)
    channel_breadcrumb_link.wait_for()
    channel_breadcrumb_link.click()

    select_table_item_checkbox(page, test_channel_name)
    click_actions_edit_link(page)
    wait_for_loading_finished(page)

    channel_name_input = page.get_by_label("Name")
    channel_name_input.wait_for()
    channel_name_input.fill(test_channel_name)

    slack_webhook_input = page.get_by_label("Slack webhook URL")
    slack_webhook_input.wait_for()
    slack_webhook_input.fill("https://hooks.slack.com/services/foo/bar")

    wait_for_loading_finished(page)
    failure_on_edit_save(page, "Failed to update channel")

    open_primary_menu_link(page, "Alerting")
    click_tab_link(page, "Monitors")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    monitor_link = page.get_by_text(test_monitor_name, exact=True)
    expect(monitor_link).to_be_visible()

    monitor_link_href = re.sub(r"\?.*$", "", monitor_link.get_attribute("href"))

    monitor_link.click()

    page.wait_for_url(f"**/app/alerting{monitor_link_href}*")
    page.wait_for_url(re.compile(r".*/app/alerting#/monitors\?.*"))

    # should redirect back to main monitors page
    expect(page).to_have_url(re.compile(r"app/alerting#/monitors\?.*"))

    select_table_item_checkbox(page, test_monitor_name)
    click_actions_edit_link(page)

    page.wait_for_url(f"**/app/alerting{monitor_link_href}*")
    page.wait_for_url(re.compile(r".*/app/alerting#/monitors\?.*"))

    # should redirect back to main monitors page
    expect(page).to_have_url(re.compile(r"app/alerting#/monitors\?.*"))


def test_user_can_see_and_edit_alert_objects(user_4, page):
    def handler():
        dismiss_toast_notification_button(page)

    page.add_locator_handler(
        page.get_by_text(re.compile(r"^.*successfully updated.$")),
        handler,
    )

    log_in(user_4, page, AUTH_PROXY_URL)

    # using this tenant should not affect access to alerting objects
    switch_tenants(page, CF_ORG_3_NAME)

    open_primary_menu_link(page, "Notifications")

    # Email recipient groups

    # Verify we can view and edit the email recipient group
    click_contextual_menu_link(page, "Email recipient groups")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).to_be_visible()

    select_table_item_checkbox(page, test_email_recipient_group_name)
    click_table_edit_button(page)
    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name="Edit recipient group")).to_be_visible()

    click_save_button(page)
    wait_for_loading_finished(page)
    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_role("heading", name="Email recipient groups", exact=True)
    ).to_be_visible()
    expect(
        page.get_by_text(test_email_recipient_group_name, exact=True)
    ).to_be_visible()

    # Email senders
    click_contextual_menu_link(page, "Email senders")
    wait_for_loading_finished(page)

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(page.get_by_text(test_email_smtp_sender_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, test_email_smtp_sender_name)
    click_table_edit_button(page)
    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name="Edit SMTP sender")).to_be_visible()

    click_save_button(page)
    wait_for_loading_finished(page)
    update_rows_per_table(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_role("heading", name="Email senders", exact=True)
    ).to_be_visible()
    expect(page.get_by_text(test_email_smtp_sender_name, exact=True)).to_be_visible()

    # Channels

    # Verify we can view and edit the notification channel
    click_contextual_menu_link(page, "Channels")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    channel_link = page.get_by_role("link", name=test_channel_name, exact=True)
    expect(channel_link).to_be_visible()
    channel_link.click()

    expect(
        page.get_by_role("heading", name=test_channel_name, exact=True)
    ).to_be_visible()

    click_actions_edit_link(page)
    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name="Edit channel")).to_be_visible()

    click_save_button(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_role("heading", name=test_channel_name, exact=True)
    ).to_be_visible()

    # Verify we can view and edit the alert monitor
    open_primary_menu_link(page, "Alerting")

    click_tab_link(page, "Monitors")

    update_rows_per_table(page)
    wait_for_loading_finished(page)

    monitor_link = page.get_by_text(test_monitor_name, exact=True)
    expect(monitor_link).to_be_visible()
    monitor_link.click()

    expect(
        page.get_by_role("heading", name=test_monitor_name, exact=True)
    ).to_be_visible()

    wait_for_loading_finished(page)

    monitor_edit_button = page.get_by_role("button", name="Edit", exact=True)
    expect(monitor_edit_button).to_be_visible()
    expect(monitor_edit_button).to_be_enabled()
    monitor_edit_button.click()

    wait_for_loading_finished(page)

    click_save_button(page)
    wait_for_loading_finished(page)

    expect(
        page.get_by_role("heading", name=test_monitor_name, exact=True)
    ).to_be_visible()


def test_user_can_delete_alerts(user_1, page):
    def handler():
        dismiss_toast_notification_button(page)

    page.add_locator_handler(
        page.get_by_text(
            re.compile(r"^.*(successfully deleted|deleted successfully).$")
        ),
        handler,
    )

    log_in(user_1, page, AUTH_PROXY_URL)

    switch_tenants(page, CF_ORG_1_NAME)

    open_primary_menu_link(page, "Alerting")

    click_tab_link(page, "Monitors")

    delete_alert_monitor(page, test_monitor_name)

    open_primary_menu_link(page, "Notifications")

    click_contextual_menu_link(page, "Channels")

    delete_notifications_channel(page, test_channel_name)

    click_contextual_menu_link(page, "Email recipient groups")

    delete_email_recipient_group(page, test_email_recipient_group_name)

    click_contextual_menu_link(page, "Email senders")

    delete_email_smtp_sender(page, test_email_smtp_sender_name)
