# Opensearch logs deployment

This repo contains the pipeline and [BOSH](https://bosh.io) manifests for deploying cloud.gov [Opensearch](https://opensearch.org/) implementation.

## UAA Setup

To set up the UAA client, add the following to the CF secrets:

```yaml
properties:
  uaa:
    clients:
      opensearch_dashboards_oauth2_client:
        secret: CHANGEME
        scope: scim.userids,cloud_controller.read,openid,oauth.approvals
        authorized-grant-types: refresh_token,authorization_code
        redirect-uri: https://CHANGEME/login
        autoapprove: true
```

## e2e tests with Playwright

This project includes e2e tests for logging into OpenSearch that use Python Playwright. To run these tests:

```shell
cp .env-sample .env # Update values in .env afterwards
./scripts/e2e-local.sh
```

## Downloading test results from CI

When the e2e tests run in CI, traces from failed test runs may be created. To download these traces, use the provided script:

```shell
./scripts/download-e2e-ci-results.sh <BUILD_NUMBER> [ENVIRONMENT]
```

where:

- `BUILD_NUMBER` - the number of the failed `smoke-tests-login-<environment>` job from the pipeline
- `ENVIRONMENT` - **optionally** specify the environment for the tests: `development`, `staging`, or `production`. defaults to `production`.

To view downloaded trace files:

```shell
source venv/bin/activate
pip install -r requirements-test.txt
playwright show-trace ci-test-results/<dir>/trace.zip
```

where `<dir>` is an arbitrary directory name generated for the test run by Playwright.

See <https://playwright.dev/python/docs/trace-viewer> for more information about working with Playwright traces.
