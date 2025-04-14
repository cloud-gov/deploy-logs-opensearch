from playwright.sync_api import expect
import re


def wait_for_channels_header(page):
    channels_header = page.get_by_role(
        "heading", name=re.compile(r"^Channels\s\([0-9]+\)$")
    )
    channels_header.wait_for()


def wait_for_email_recipient_groups_header(page):
    recipient_groups_header = page.get_by_role(
        "heading", name=re.compile(r"^Email recipient groups$")
    )
    recipient_groups_header.wait_for()


def create_email_recipient_group(page, user, email_recipient_group_name):
    create_group_button = (
        page.locator("div")
        .filter(has_text=re.compile(r"^Create recipient group$"))
        .get_by_role("link")
    )
    create_group_button.wait_for()
    create_group_button.click()

    group_name_input = page.get_by_placeholder("Enter recipient group name")
    group_name_input.wait_for()
    group_name_input.fill(email_recipient_group_name)

    email_address_input = page.locator(
        'css=input[data-test-subj="comboBoxSearchInput"]'
    )
    email_address_input.fill(user.username)
    page.keyboard.press("Enter")

    create_group_button = page.get_by_role("button", name="Create")
    create_group_button.wait_for()
    create_group_button.click()

    email_recipient_groups_header = page.get_by_role(
        "heading", name="Email recipient groups"
    )
    email_recipient_groups_header.wait_for()

    created_recipient_group = page.get_by_text(email_recipient_group_name, exact=True)
    created_recipient_group.wait_for()


def create_notifications_channel(page, email_recipient_group_name, channel_name):
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

    cloud_smtp_sender = page.get_by_role("option", name="cloudgovemail")
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

    created_channel = page.get_by_role("link", name=channel_name, exact=True)
    created_channel.wait_for()


def create_alert_monitor(page, monitor_name, trigger_name, action_name, channel_name):
    monitor_link = page.get_by_role("tab", name="Monitors")
    monitor_link.wait_for()
    monitor_link.click()

    create_monitor_button = page.get_by_role("link", name="Create monitor")
    create_monitor_button.wait_for()
    create_monitor_button.click()

    monitor_name_input = page.locator('input[name="name"]')
    monitor_name_input.wait_for()
    monitor_name_input.fill(monitor_name)

    index_input = page.locator("#index")
    index_input.wait_for()
    index_input.fill("logs-app*")
    page.keyboard.press("Enter")

    time_input_placeholder = (
        page.locator("div").filter(has_text=re.compile(r"^Select a time field$")).first
    )
    time_input_placeholder.wait_for()
    time_input_placeholder.click()

    timestamp_option = page.get_by_role("option", name="@timestamp")
    timestamp_option.wait_for()
    timestamp_option.click()

    add_trigger_button = page.get_by_role("button", name="Add trigger", exact=True)
    add_trigger_button.wait_for()
    add_trigger_button.click()

    trigger_name_input = page.locator('input[name="triggerDefinitions[0].name"]')
    trigger_name_input.wait_for()
    trigger_name_input.fill(trigger_name)

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

    monitor_name_heading = page.get_by_role("heading", name=monitor_name, exact=True)
    monitor_name_heading.wait_for()

    monitor_enabled_text = page.get_by_text("Enabled")
    monitor_enabled_text.wait_for()


def delete_notifications_channel(page, channel_name):
    channel_checkbox = (
        page.locator("tr").filter(has_text=channel_name).get_by_role("checkbox")
    )
    channel_checkbox.wait_for()
    channel_checkbox.click()

    actions_button = page.get_by_role("button", name="Actions")
    actions_button.wait_for()
    actions_button.click()

    delete_channel_button = page.get_by_role("button", name="Delete", exact=True)
    delete_channel_button.wait_for()
    delete_channel_button.click()

    delete_confirm_input = page.get_by_placeholder("delete")
    delete_confirm_input.wait_for()
    delete_confirm_input.fill("delete")

    delete_confirm_button = page.get_by_role("button", name="Delete", exact=True)
    delete_confirm_button.wait_for()
    delete_confirm_button.click()

    wait_for_channels_header(page)

    expect(page.get_by_role("heading", name="No channels to display")).to_be_visible()


def delete_email_recipient_group(page, recipient_group_name):
    recipient_group_checkbox = (
        page.locator("tr").filter(has_text=recipient_group_name).get_by_role("checkbox")
    )
    recipient_group_checkbox.wait_for()
    recipient_group_checkbox.click()

    delete_channel_button = page.get_by_role("button", name="Delete", exact=True)
    delete_channel_button.wait_for()
    delete_channel_button.click()

    delete_confirm_input = page.get_by_placeholder("delete")
    delete_confirm_input.wait_for()
    delete_confirm_input.fill("delete")

    delete_confirm_button = page.get_by_role("button", name="Delete", exact=True)
    delete_confirm_button.wait_for()
    delete_confirm_button.click()

    wait_for_email_recipient_groups_header(page)

    expect(
        page.get_by_role("heading", name="No recipient groups to display")
    ).to_be_visible()
