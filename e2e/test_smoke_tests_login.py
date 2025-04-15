#!/usr/bin/env python

import re
import logging
from playwright.sync_api import expect
from urllib.parse import urljoin

from .utils import log_in
from . import AUTH_PROXY_URL

logging.basicConfig(level=logging.DEBUG)


def test_user_login(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)
    expect(page).to_have_url(re.compile(f"{urljoin(AUTH_PROXY_URL, 'app/home')}.*"))
