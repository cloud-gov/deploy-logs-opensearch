#!/bin/bash

set -e -u

cd release-git-repo

RELEASE_NAME=$(grep final_name config/final.yml | awk '{print $2}')

tar -zxf "../final-builds-dir-tarball/final-builds-dir-${RELEASE_NAME}.tgz"
tar -zxf "../releases-dir-tarball/releases-dir-${RELEASE_NAME}.tgz"
cat <<EOF > "config/private.yml"
$PRIVATE_YML_CONTENT
EOF

bosh-cli -n create-release --force --timestamp-version
bosh-cli upload-release

latest_release=$(echo dev_releases/"${RELEASE_NAME}"/"${RELEASE_NAME}"*.yml | grep -oE '[0-9]+\+dev\.[0-9]+.yml' | sed -e 's/\.yml$//' | sort -V | tail -1)
mv "${RELEASE_NAME}.tgz" "../finalized-release/${RELEASE_NAME}-${latest_release}.tgz"
