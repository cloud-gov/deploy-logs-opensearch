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
TEST_RELEASE_TARBALL_NAME="$RELEASE_NAME-test-$TIMESTAMP"

bosh-cli -n create-release --force --timestamp-version --tarball "$TEST_RELEASE_TARBALL_NAME.tgz"

mv "$TEST_RELEASE_TARBALL_NAME.tgz" "../finalized-release/$TEST_RELEASE_TARBALL_NAME.tgz"
