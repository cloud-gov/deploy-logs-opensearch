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
