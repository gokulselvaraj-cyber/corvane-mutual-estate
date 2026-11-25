#!/usr/bin/env bash
# ONE-OFF (2025-06-12): replays policies.bound.v1 for 312 policies whose welcome email bounced during the
# SMTP relay outage (INC-0611). Kept for the incident record; never run again.
set -euo pipefail
: "${KAFKA_BOOTSTRAP:?}"
while read -r policy; do
  kcat -b "$KAFKA_BOOTSTRAP" -t policies.bound.v1 -P -k "$policy" <<< "$(psql "$POLICY_DSN" -Atc \
    "select row_to_json(p) from policy.v_bound_event p where policy_number = '$policy'")"
done < "${1:-bounced_policies.txt}"
