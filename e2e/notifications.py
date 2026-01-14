from playwright.sync_api import expect
import re

from .utils import (
    wait_for_header,
    click_delete_button,
    fill_delete_confirm_placeholder,
    click_delete_button,
    select_table_item_checkbox,
    open_actions_menu,
    wait_for_loading_finished,
    update_rows_per_table,
    dismiss_toast_notifications,
    click_save_button,
)

from . import SMTP_SENDER_HOST, SMTP_SENDER_PORT, SMTP_SENDER_FROM


def wait_for_channels_header(page):
    wait_for_header(page, re.compile(r"^Channels\s\([0-9]+\)$"))


def fill_email_recipient_group_details(page, user, email_recipient_group_name):
    group_name_input = page.get_by_placeholder("Enter recipient group name")
    group_name_input.wait_for()
    group_name_input.fill(email_recipient_group_name)

    email_address_input = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Email addresses$"))
        .get_by_role("textbox")
    )
    email_address_input.fill(user.username)
    page.keyboard.press("Enter")


def create_email_recipient_group(page, user, email_recipient_group_name):
    create_group_button = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Create recipient group$"))
        .get_by_role("link")
    )
    create_group_button.wait_for()
    create_group_button.click()

    fill_email_recipient_group_details(page, user, email_recipient_group_name)

    create_group_button = page.get_by_role("button", name="Create")
    create_group_button.wait_for()
    create_group_button.click()

    wait_for_header(page, "Email recipient groups")

    update_rows_per_table(page)

    wait_for_loading_finished(page)

    expect(page.get_by_text(email_recipient_group_name, exact=True)).to_be_visible()


def fill_email_smtp_sender_details(page, email_sender_name):
    sender_name_input = page.get_by_placeholder("Enter sender name")
    sender_name_input.wait_for()
    sender_name_input.fill(email_sender_name)

    sender_email_input = page.get_by_label("Email address")
    sender_email_input.wait_for()
    sender_email_input.fill(SMTP_SENDER_FROM)

    sender_host_input = page.get_by_label("Host")
    sender_host_input.wait_for()
    sender_host_input.fill(SMTP_SENDER_HOST)

    sender_host_input = page.get_by_label("Port")
    sender_host_input.wait_for()
    sender_host_input.fill(SMTP_SENDER_PORT)


def create_email_smtp_sender(page, email_sender_name):
    create_group_button = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Create SMTP sender$"))
        .get_by_role("link")
    )
    create_group_button.wait_for()
    create_group_button.click()

    fill_email_smtp_sender_details(page, email_sender_name)

    create_group_button = page.get_by_role("button", name="Create")
    create_group_button.wait_for()
    create_group_button.click()

    wait_for_header(page, "Email senders")

    update_rows_per_table(page)

    wait_for_loading_finished(page)

    expect(page.get_by_text(email_sender_name, exact=True)).to_be_visible()


def create_notifications_channel(
    page, email_recipient_group_name, email_sender_name, channel_name
):
    create_channel_button = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Create channel$"))
        .get_by_role("link")
    )
    create_channel_button.wait_for()
    create_channel_button.click()

    channel_name_input = page.get_by_label("Name")
    channel_name_input.wait_for()
    channel_name_input.fill(channel_name)

    # this is probably brittle because it assumes that Slack is the
    # default option for a channel, which could change. but the markup
    # here is not accessible and easy to select otherwise
    channel_type_button = page.get_by_role("button", name="Slack")
    channel_type_button.wait_for()
    channel_type_button.click()

    email_option = page.get_by_role("option", name="Email")
    email_option.wait_for()
    email_option.click()

    choose_sender_placeholder = (
        page.locator("div").filter(has_text=re.compile(r"^Sender name$")).first
    )
    choose_sender_placeholder.wait_for()
    choose_sender_placeholder.click()

    cloud_smtp_sender = page.get_by_role("option", name=email_sender_name)
    cloud_smtp_sender.wait_for()
    cloud_smtp_sender.click()

    enter_recipient_group_div = page.locator("div").filter(
        has_text=re.compile(r"^Email address, recipient group name$")
    )
    enter_recipients_placeholder = enter_recipient_group_div.first
    enter_recipients_placeholder.wait_for()
    enter_recipients_placeholder.click()

    recipient_group_input = page.get_by_label("Default recipients")
    recipient_group_input.wait_for()
    recipient_group_input.fill(email_recipient_group_name)
    page.keyboard.press("Enter")

    create_channel_button = page.get_by_role("button", name="Create", exact=True)
    create_channel_button.wait_for()
    create_channel_button.click()

    wait_for_channels_header(page)

    expect(page.get_by_role("link", name=channel_name, exact=True)).to_be_visible()


def create_alert_monitor(page, monitor_name, trigger_name, action_name, channel_name):
    create_monitor_button = page.get_by_role("link", name="Create monitor").first
    create_monitor_button.wait_for()
    create_monitor_button.click()

    monitor_name_input = page.locator('input[name="name"]')
    monitor_name_input.wait_for()
    monitor_name_input.fill(monitor_name)

    index_input = page.locator("#index")
    index_input.wait_for()
    index_input.fill("logs-app-*")
    page.keyboard.press("Enter")

    wait_for_loading_finished(page)

    time_field_input = page.locator("#timeField")
    time_field_input.wait_for()
    time_field_input.fill("@timestamp")
    page.keyboard.press("Enter")

    wait_for_loading_finished(page)

    add_trigger_button = page.get_by_role("button", name="Add trigger", exact=True)
    add_trigger_button.wait_for()
    add_trigger_button.click()

    wait_for_loading_finished(page)

    trigger_name_input = page.locator('input[name="triggerDefinitions[0].name"]')
    trigger_name_input.wait_for()
    trigger_name_input.fill(trigger_name)

    query_time_interval = page.locator('input[name="bucketValue"]')
    query_time_interval.wait_for()
    query_time_interval.fill("15")

    wait_for_loading_finished(page)

    query_time_interval_unit_select = page.locator("#bucketUnitOfTime")
    query_time_interval_unit_select.wait_for()
    query_time_interval_unit_select.select_option(label="minute(s)")

    wait_for_loading_finished(page)

    trigger_threshold_input = page.locator(
        'input[name="triggerDefinitions[0].thresholdValue"]'
    )
    trigger_threshold_input.wait_for()
    # set threshold to 1 billion records for alert to trigger so that e2e tests for
    # access do not actually trigger alerts
    trigger_threshold_input.fill("1000000000")

    wait_for_loading_finished(page)

    action_name_input = page.get_by_placeholder("Enter action name")
    action_name_input.wait_for()
    action_name_input.fill(action_name)

    select_channel_placeholder = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Select channel to notify$"))
        .first
    )
    select_channel_placeholder.wait_for()
    select_channel_placeholder.click()

    wait_for_loading_finished(page)

    action_channel_input = page.locator(
        '[id="triggerDefinitions\\[0\\]\\.actions\\.0\\.destination_id"]'
    )
    action_channel_input.wait_for()
    action_channel_input.fill(channel_name)

    action_channel_option = page.get_by_text(f"[Channel] {channel_name}").first
    action_channel_option.wait_for()
    action_channel_option.click()

    create_monitor_button = page.get_by_role("button", name="Create", exact=True)
    create_monitor_button.wait_for()
    create_monitor_button.click()

    wait_for_loading_finished(page)

    expect(page.get_by_role("heading", name=monitor_name, exact=True)).to_be_visible()
    expect(page.get_by_text("Enabled")).to_be_visible()


def delete_notifications_channel(page, channel_name):
    expect(page.get_by_text(channel_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, channel_name)

    open_actions_menu(page)

    click_delete_button(page)

    fill_delete_confirm_placeholder(page)

    click_delete_button(page)

    wait_for_channels_header(page)

    expect(page.get_by_text(channel_name, exact=True)).not_to_be_visible()


def delete_email_recipient_group(page, recipient_group_name):
    expect(page.get_by_text(recipient_group_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, recipient_group_name)

    delete_recipient_group_button = page.get_by_role(
        "button", name="Delete", exact=True
    )
    delete_recipient_group_button.wait_for()
    delete_recipient_group_button.click()

    fill_delete_confirm_placeholder(page)

    click_delete_button(page)

    wait_for_header(page, re.compile(r"^Email recipient groups$"))

    expect(page.get_by_text(recipient_group_name, exact=True)).not_to_be_visible()


def delete_email_smtp_sender(page, email_sender_name):
    expect(page.get_by_text(email_sender_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, email_sender_name)

    delete_email_smtp_sender_button = page.get_by_role(
        "button", name="Delete", exact=True
    ).first
    delete_email_smtp_sender_button.wait_for()
    delete_email_smtp_sender_button.click()

    fill_delete_confirm_placeholder(page)

    click_delete_button(page)

    wait_for_header(page, re.compile(r"^Email senders$"))

    expect(page.get_by_text(email_sender_name, exact=True)).not_to_be_visible()


def delete_alert_monitor(page, monitor_name):
    expect(page.get_by_text(monitor_name, exact=True)).to_be_visible()

    select_table_item_checkbox(page, monitor_name)

    open_actions_menu(page)

    click_delete_button(page)

    click_delete_button(page)

    wait_for_header(page, "Monitors")

    expect(page.get_by_text(monitor_name, exact=True)).not_to_be_visible()


def failure_on_edit_save(page, expected_failure_message):
    dismiss_toast_notifications(page)

    click_save_button(page)

    failure_message = page.get_by_text(expected_failure_message)
    expect(failure_message).to_be_visible()

    dismiss_toast_notifications(page)

    cancel_button = page.get_by_role("link", name="Cancel")
    cancel_button.wait_for()
    cancel_button.click()
