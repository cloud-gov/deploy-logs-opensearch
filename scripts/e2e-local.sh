#!/usr/bin/env bash

set -o allexport
source ".env"
set +o allexport

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

"$dir"/e2e.sh --headed
