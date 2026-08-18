#!/usr/bin/env bash

set -e

# Login to UAA
uaac target "$UAA_API_URL"
uaac token client get "$UAA_CLIENT_ID" -s "$UAA_CLIENT_SECRET"

TEST_USER_CREDENTIAL_NAMES=$(echo "$TEST_USERS_CREDENTIAL_USERNAME_MAP" | jq '. | keys | join(" ")')

for credential_name in $TEST_USER_CREDENTIAL_NAMES; do
  credential_name=$(echo "$credential_name" | tr -d '"')

  printf "updating password credential for %s\n\n" "$credential_name"

  # Generate a new password for the credential
  PASSWORD_CREDENTIAL="/concourse/main/deploy-logs-opensearch/$credential_name"
  if ! credhub get -n "$PASSWORD_CREDENTIAL" > /dev/null; then
    credhub generate -n "$PASSWORD_CREDENTIAL" --type password
  else 
    credhub regenerate -n "$PASSWORD_CREDENTIAL"
  fi
  
  # Get the UAA username for the corresponding Credhub credential
  USERNAME=$(echo "$TEST_USERS_CREDENTIAL_USERNAME_MAP" | jq -r --arg credential_name "$credential_name" '.[$credential_name]')

  # Get the new password from Credhub
  PASSWORD=$(credhub get -n "$PASSWORD_CREDENTIAL" --output-json | jq -r '.value')

  if ! uaac user get "$USERNAME" > /dev/null; then
    printf "Creating UAA user %s\n\n" "$USERNAME"
    uaac user add "$USERNAME" --password "$PASSWORD" --origin cloud.gov --emails "$USERNAME"
  else
    printf "updating UAA password for %s\n\n" "$USERNAME"

    # Update the user password in UAA with the new value from Credhub
    uaac password set "$USERNAME" --password "$PASSWORD"  
  fi

  # Activate the user, just to be safe
  uaac user activate "$USERNAME"
done



