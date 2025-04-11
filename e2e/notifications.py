import re


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

    recipient_group = page.get_by_text(email_recipient_group_name)
    recipient_group.wait_for()


def create_notifications_channel(page, channel_name):
    create_channel_button = page.get_by_text("Create channel")
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

    email_option = page.get_by_text("Email")
    email_option.wait_for()
    email_option.click()

    choose_sender_label = page.get_by_text("Sender")
    choose_sender_label.wait_for()
    choose_sender_label.click()

    cloud_smtp_sender = page.get_by_text("cloudgovemail")
    cloud_smtp_sender.wait_for()
    cloud_smtp_sender.click()
