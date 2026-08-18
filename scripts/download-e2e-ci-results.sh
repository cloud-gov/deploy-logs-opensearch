#!/usr/bin/env bash

BUILD_NUMBER=$1

if [[ -z "$BUILD_NUMBER" ]]; then
  echo "build number is required as first argument"
  exit 1
fi

ENVIRONMENT=${2:-production}

CI_TASK_TARGET="fly -t ${FLY_TARGET:=ci} intercept -j deploy-logs-opensearch/e2e-tests-$ENVIRONMENT -s e2e-tests -b $BUILD_NUMBER"
TEST_RESULTS_DIR="deploy-logs-opensearch-config/test-results"
LOCAL_TARGET_DIR="ci-test-results"

for test_dir in $($CI_TASK_TARGET -- ls $TEST_RESULTS_DIR); do
  echo "found test dir: $test_dir"

  for file in $($CI_TASK_TARGET -- ls "$TEST_RESULTS_DIR/$test_dir"); do
    mkdir -p "$LOCAL_TARGET_DIR/$test_dir"
    $CI_TASK_TARGET -- cat "$TEST_RESULTS_DIR/$test_dir/$file" > "$LOCAL_TARGET_DIR/$test_dir/$file"
    echo "downloaded $file"
  done
done
