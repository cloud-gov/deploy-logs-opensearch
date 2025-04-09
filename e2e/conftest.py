from os import getenv

import pytest

from .user import User


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
