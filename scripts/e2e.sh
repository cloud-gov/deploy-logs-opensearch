#!/usr/bin/env bash

python -m venv venv
source venv/bin/activate
pip install -r ci/requirements.txt
playwright install firefox
python -m pytest ci --browser firefox --tracing retain-on-failure    
