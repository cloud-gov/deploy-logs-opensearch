#!/usr/bin/env python

from .utils import log_in, switch_tenants
from . import AUTH_PROXY_URL, CF_ORG_1_NAME


def test_user_can_create_alerts(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)
    switch_tenants(page, CF_ORG_1_NAME)
