#!/usr/bin/env bash

python -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install -r requirements-test.txt
playwright install chromium
python -m pytest e2e --browser chromium --tracing retain-on-failure "$@"
