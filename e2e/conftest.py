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


@pytest.fixture
def user_2():
    user_2_username = getenv(f"TEST_USER_2_USERNAME")
    user_2_password = getenv(f"TEST_USER_2_PASSWORD")
    user_2_totp_seed = getenv(f"TEST_USER_2_TOTP_SEED")
    user_2 = User(
        user_2_username,
        user_2_password,
        user_2_totp_seed,
    )
    return user_2


@pytest.fixture
def user_3():
    user_3_username = getenv(f"TEST_USER_3_USERNAME")
    user_3_password = getenv(f"TEST_USER_3_PASSWORD")
    user_3_totp_seed = getenv(f"TEST_USER_3_TOTP_SEED")
    user_3 = User(
        user_3_username,
        user_3_password,
        user_3_totp_seed,
    )
    return user_3


@pytest.fixture
def user_4():
    user_4_username = getenv(f"TEST_USER_4_USERNAME")
    user_4_password = getenv(f"TEST_USER_4_PASSWORD")
    user_4_totp_seed = getenv(f"TEST_USER_4_TOTP_SEED")
    user_4 = User(
        user_4_username,
        user_4_password,
        user_4_totp_seed,
    )
    return user_4
