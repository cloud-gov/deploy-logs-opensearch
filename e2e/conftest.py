from os import getenv
from playwright.sync_api import expect

import pytest

from .user import User

expect.set_options(timeout=60_000)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    browser_context_args["locale"] = "en-US"
    return {
        **browser_context_args,
    }


@pytest.fixture
def user_1():
    user_1_username = getenv(f"TEST_USER_1_USERNAME")
    user_1_password = getenv(f"TEST_USER_1_PASSWORD")
    user_1_totp_seed = getenv(f"TEST_USER_1_TOTP_SEED")
    user_1 = User(
        user_1_username,
        user_1_password,
        user_1_totp_seed,
    )
    return user_1
