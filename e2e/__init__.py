import os
import sys

required_env_vars = [
    "AUTH_PROXY_URL",
    "UAA_BASE_URL",
    "CF_ORG_1_NAME",
    "TEST_USER_1_USERNAME",
    "TEST_USER_1_PASSWORD",
    "TEST_USER_1_TOTP_SEED",
]

for env_var in required_env_vars:
    if os.environ[env_var] is None:
        print(f"{env_var} is a required environment variable, exiting")
        sys.exit(1)

AUTH_PROXY_URL = os.environ["AUTH_PROXY_URL"]
UAA_BASE_URL = os.environ["AUTH_PROXY_URL"]
CF_ORG_1_NAME = os.environ["CF_ORG_1_NAME"]
