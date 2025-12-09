import os
import sys

required_env_vars = [
    "AUTH_PROXY_URL",
    "UAA_BASE_URL",
    "CF_ORG_1_NAME",
    "CF_ORG_2_NAME",
    "CF_ORG_3_NAME",
    "TEST_USER_1_USERNAME",
    "TEST_USER_1_PASSWORD",
    "TEST_USER_1_TOTP_SEED",
    "TEST_USER_2_USERNAME",
    "TEST_USER_2_PASSWORD",
    "TEST_USER_2_TOTP_SEED",
    "TEST_USER_3_USERNAME",
    "TEST_USER_3_PASSWORD",
    "TEST_USER_3_TOTP_SEED",
    "TEST_USER_4_USERNAME",
    "TEST_USER_4_PASSWORD",
    "TEST_USER_4_TOTP_SEED",
    "SMTP_SENDER_HOST",
    "SMTP_SENDER_PORT",
    "SMTP_SENDER_FROM",
]

for env_var in required_env_vars:
    if os.environ[env_var] is None:
        print(f"{env_var} is a required environment variable, exiting")
        sys.exit(1)

AUTH_PROXY_URL = os.environ["AUTH_PROXY_URL"]
UAA_BASE_URL = os.environ["AUTH_PROXY_URL"]
CF_ORG_1_NAME = os.environ["CF_ORG_1_NAME"]
CF_ORG_2_NAME = os.environ["CF_ORG_2_NAME"]
CF_ORG_3_NAME = os.environ["CF_ORG_3_NAME"]
SMTP_SENDER_HOST = os.environ["SMTP_SENDER_HOST"]
SMTP_SENDER_PORT = os.environ["SMTP_SENDER_PORT"]
SMTP_SENDER_FROM = os.environ["SMTP_SENDER_FROM"]
