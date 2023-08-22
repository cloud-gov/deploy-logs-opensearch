# 18F cloud.gov ELK deployment

This repo contains the pipeline and [BOSH](https://bosh.io) manifests for deploying cloud.gov [ELK](https://www.elastic.co/videos/introduction-to-the-elk-stack) implementation.

### Admin Setup
For admins to access all logs, membership in the [System Organization](https://github.com/18F/cg-deploy-opensearch/blob/cf9271ae1ff2bc0464ca57a87b76e9ffc7ce01ab/opensearch-jobs.yml#L201) is required.

### UAA Setup

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
      opensearch_firehose_ingestor:
        secret: CHANGEME
        authorized-grant-types: client_credentials
        authorities: doppler.firehose,cloud_controller.admin
        override: true
```
