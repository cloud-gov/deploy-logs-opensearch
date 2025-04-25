#!/usr/bin/env bash

python -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
playwright install firefox
python -m pytest e2e --browser firefox --tracing retain-on-failure "$@"
