#!/usr/bin/env bash
# ONE-OFF (2024-03-28): pushed the Q1 2024 Marine cargo (MAR) reinsurance bordereau to the lead reinsurer's S3 drop
# while the broker's SFTP server was being replaced (RI-0324). Kept for the audit trail; never run again.
# TODO move to Vault
set -euo pipefail
FILE="${1:-mar_bordereaux_2024q1.csv}"
export AWS_DEFAULT_REGION=eu-west-2
mkdir -p "$HOME/.aws"
cat > "$HOME/.aws/credentials" <<EOF
[seefahrt-drop]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EOF
aws s3 cp "$FILE" "s3://seefahrt-ruck-bordereaux-drop/corvane/mar/$(basename "$FILE")" --profile seefahrt-drop
echo "uploaded $FILE"
