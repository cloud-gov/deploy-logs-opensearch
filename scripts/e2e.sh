#!/usr/bin/env bash

set -o allexport
source ".env"
set +o allexport
python -m pytest ci --browser firefox --tracing retain-on-failure    
