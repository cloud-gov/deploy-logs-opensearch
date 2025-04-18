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

function escape_username() {
  USERNAME_ESCAPED=$(echo "$1" | jq -Rr @uri)
  echo "$USERNAME_ESCAPED"
}

function get_user_guid() {
  USERNAME_ESCAPED=$(escape_username "$1")
  USER_GUID=$(cf curl "/v3/users?partial_usernames=$USERNAME_ESCAPED" | jq -er '.resources[0].guid')
  echo "$USER_GUID"
}

function set_org_user() {
  USER_GUID=$(get_user_guid "$1")
  ORG_GUID=$(cf org "$2" --guid)
  TMP_FILE=$(mktemp)

  COUNT_ORG_USER_ROLES=$(cf curl "/v3/roles?organization_guids=$ORG_GUID&user_guids=$USER_GUID&types=organization_user" | jq -r '.pagination.total_results')
  if [[ $COUNT_ORG_USER_ROLES -gt 0 ]]; then
    echo "user already has organization_user role in $2, continuing"
    return
  fi

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
    -d "@$TMP_FILE" \
    --fail > /dev/null
  
  rm "$TMP_FILE"
}

function delete_sandbox_org_roles() {
  SANDBOX_ORG="sandbox-$(echo "$1" | cut -d '@' -f2 | cut -d '.' -f1)"
  if ! cf org "$SANDBOX_ORG" > /dev/null; then
    return
  fi

  SANDBOX_SPACE=$(echo "$1" | cut -d '@' -f1)
  if ! cf space "$SANDBOX_SPACE" > /dev/null; then
    return
  fi

  SANDBOX_ORG_GUID=$(cf org "$SANDBOX_ORG" --guid)
  USER_GUID=$(get_user_guid "$1")

  for space_role in SpaceManager SpaceDeveloper SpaceAuditor; do
    cf unset-space-role "$1" "$SANDBOX_ORG" "$SANDBOX_SPACE" "$space_role"
  done

  for role_guid in $(cf curl "/v3/roles?organization_guids=$SANDBOX_ORG_GUID&user_guids=$USER_GUID" | jq -r '.resources[].guid'); do
    cf curl "/v3/roles/$role_guid" -X DELETE
  done
}

# Expected results:
#  - User 1 is in org 1 and org 3
#  - User 2 is in org 2. User 2 shares no orgs with User 1.
#  - User 3 is in org 1. User 3 shares 1 org with User 1.
#  - User 4 is in org 1 and org 3. User 4 shares all orgs with User 1.

cf create-org "$CF_ORG_1_NAME"
cf create-org "$CF_ORG_2_NAME"
cf create-org "$CF_ORG_3_NAME"

# Delete sandbox org roles for test users so we can be sure that
# their only orgs are the ones we have provisioned
delete_sandbox_org_roles "$TEST_USER_1_USERNAME"
delete_sandbox_org_roles "$TEST_USER_2_USERNAME"
delete_sandbox_org_roles "$TEST_USER_3_USERNAME"
delete_sandbox_org_roles "$TEST_USER_4_USERNAME"

# User 1 is an org manager in org 1 and org 3
cf set-org-role "$TEST_USER_1_USERNAME" "$CF_ORG_1_NAME" OrgManager
set_org_user "$TEST_USER_1_USERNAME" "$CF_ORG_1_NAME"
cf set-org-role "$TEST_USER_1_USERNAME" "$CF_ORG_3_NAME" OrgManager
set_org_user "$TEST_USER_1_USERNAME" "$CF_ORG_3_NAME"

# User 2 is an org manager in org 2
cf set-org-role "$TEST_USER_2_USERNAME" "$CF_ORG_2_NAME" OrgManager
set_org_user "$TEST_USER_2_USERNAME" "$CF_ORG_2_NAME"

# User 3 is an org manager in org 1
cf set-org-role "$TEST_USER_3_USERNAME" "$CF_ORG_1_NAME" OrgManager
set_org_user "$TEST_USER_3_USERNAME" "$CF_ORG_1_NAME"

# User 4 is an org manager in org 1 and org 3
cf set-org-role "$TEST_USER_4_USERNAME" "$CF_ORG_1_NAME" OrgManager
set_org_user "$TEST_USER_4_USERNAME" "$CF_ORG_1_NAME"
cf set-org-role "$TEST_USER_4_USERNAME" "$CF_ORG_3_NAME" OrgManager
set_org_user "$TEST_USER_4_USERNAME" "$CF_ORG_3_NAME"

