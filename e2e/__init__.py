import os
import sys

if os.environ["CF_SYSTEM_DOMAIN"] is None:
    print("CF_SYSTEM_DOMAIN is a required environment variable, exiting")
    sys.exit(1)

AUTH_PROXY_URL = "https://logs.{}".format(os.environ["CF_SYSTEM_DOMAIN"])
UAA_BASE_URL = "https://login.{}".format(os.environ["CF_SYSTEM_DOMAIN"])
