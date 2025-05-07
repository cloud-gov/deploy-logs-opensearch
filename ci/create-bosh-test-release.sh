#!/bin/bash

set -e -u

cd release-git-repo

RELEASE_NAME=$(grep final_name config/final.yml | awk '{print $2}')

tar -zxf "../final-builds-dir-tarball/final-builds-dir-${RELEASE_NAME}.tgz"
tar -zxf "../releases-dir-tarball/releases-dir-${RELEASE_NAME}.tgz"
cat <<EOF > "config/private.yml"
$PRIVATE_YML_CONTENT
EOF

TIMESTAMP=$(date +%s)
TEST_RELEASE_TARBALL_NAME="$RELEASE_NAME-test-$TIMESTAMP.tgz"

bosh-cli -n create-release --force --tarball "$TEST_RELEASE_TARBALL_NAME"

mv "$TEST_RELEASE_TARBALL_NAME" "../finalized-release/$TEST_RELEASE_TARBALL_NAME.tgz"
