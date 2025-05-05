#!/bin/bash

bosh interpolate \
  deploy-logs-opensearch-test-config/varsfiles/terraform.yml \
  -l terraform-yaml/state.yml \
  > terraform-secrets/terraform.yml
