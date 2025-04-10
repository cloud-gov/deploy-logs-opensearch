#!/usr/bin/env bash

set -e

if ! cf target > /dev/null; then
  cf api "${CF_API_URL}"
  cf auth
fi

required_env_vars=(
  TEST_USER_1_USERNAME
  TEST_USER_2_USERNAME
  TEST_USER_3_USERNAME
  TEST_USER_4_USERNAME
  CF_ORG_1_NAME
  CF_ORG_2_NAME
  CF_ORG_3_NAME
)
for var in "${required_env_vars[@]}"; do
  if [ -z "${!var+x}" ]; then
    echo "$var is a required environment variable"
    exit 1
  fi
done

function set_org_user() {
  USERNAME_ESCAPED=$(echo "$1" | jq -Rr @uri)
  USER_GUID=$(cf curl "/v3/users?partial_usernames=$USERNAME_ESCAPED" | jq -er '.resources[0].guid')
  ORG_GUID=$(cf org "$2" --guid)
  TMP_FILE=$(mktemp)

  cat > "${TMP_FILE}" << EOF
{
  "type": "organization_user",
  "relationships": {
    "user": {
      "data": {
        "guid": "$USER_GUID"
      }
    },
    "organization": {
      "data": {
        "guid": "$ORG_GUID"
      }
    }
  }
}
EOF

  cf curl "/v3/roles" \
    -X POST \
    -d "@$TMP_FILE"
  
  rm "$TMP_FILE"
}

# Expected results:
#  - User 1 is in org 1 and org 3
#  - User 2 is in org 2. User 2 shares no orgs with User 1.
#  - User 3 is in org 1. User 3 shares 1 org with User 1.
#  - User 4 is in org 1 and org 3. User 4 shares all orgs with User 1.

cf create-org "$CF_ORG_1_NAME"
cf create-org "$CF_ORG_2_NAME"
cf create-org "$CF_ORG_3_NAME"

# User 1 is an org manager in org 1 and org 3
cf set-org-role "$TEST_USER_1_USERNAME" "$CF_ORG_1_NAME" OrgManager
set_org_user "$TEST_USER_1_USERNAME" "$CF_ORG_1_NAME"
cf set-org-role "$TEST_USER_1_USERNAME" "$CF_ORG_3_NAME" OrgManager
set_org_user "$TEST_USER_1_USERNAME" "$CF_ORG_3_NAME"

# User 2 is an org manager in org 2
cf set-org-role "$TEST_USER_2_USERNAME" "$CF_ORG_2_NAME" OrgManager

# User 3 is an org manager in org 1
cf set-org-role "$TEST_USER_3_USERNAME" "$CF_ORG_1_NAME" OrgManager

# User 4 is an org manager in org 1 and org 3
cf set-org-role "$TEST_USER_4_USERNAME" "$CF_ORG_1_NAME" OrgManager
cf set-org-role "$TEST_USER_4_USERNAME" "$CF_ORG_3_NAME" OrgManager

