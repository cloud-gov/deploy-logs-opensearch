#!/usr/bin/env python

import time
from .notifications import create_email_recipient_group, create_notifications_channel
from .utils import (
    log_in,
    switch_tenants,
    open_primary_menu_link,
    click_contextual_menu_link,
)
from . import AUTH_PROXY_URL, CF_ORG_1_NAME

test_run_timestamp = int(time.time())
test_email_recipient_group_name = f"TestEmailRecipientGroup-{test_run_timestamp}"
test_channel_name = f"TestChannel-{test_run_timestamp}"


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
