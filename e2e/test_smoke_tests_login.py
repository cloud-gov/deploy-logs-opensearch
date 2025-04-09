#!/usr/bin/env python

import os
import logging

from .utils import log_in
from . import AUTH_PROXY_URL

logging.basicConfig(level=logging.DEBUG)


def test_user_login(user_1, page):
    log_in(user_1, page, AUTH_PROXY_URL)
