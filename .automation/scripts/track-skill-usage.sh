#!/usr/bin/env bash
# Skill Usage Tracker
# Records when skills are used and their outcomes for effectiveness analysis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/../logs"
METRICS_FILE="${LOGS_DIR}/skill-metrics.json"

mkdir -p "$LOGS_DIR"

# Initialize metrics file if it doesn't exist
if [[ ! -f "$METRICS_FILE" ]]; then
    echo '{"skills": {}}' > "$METRICS_FILE"
fi

usage() {
    cat <<EOF
Usage: $0 <command> <skill-name> [options]

Commands:
    use <skill>              Record skill was used
    success <skill>          Record successful outcome
    failure <skill> <reason> Record failure with reason
    stats <skill>            Show skill statistics
    all-stats                Show all skills statistics

Examples:
    $0 use deploy-validator
    $0 success deploy-validator
    $0 failure deploy-validator "lint-check-failed"
    $0 stats deploy-validator
    $0 all-stats
EOF
    exit 1
}

[[ $# -lt 2 ]] && usage

COMMAND="$1"
SKILL="${2:-}"

# Helper: Update metrics JSON
update_metrics() {
    local skill="$1"
    local metric="$2"
    local value="${3:-1}"

    python3 - <<EOF
import json
from datetime import datetime, timezone

with open("$METRICS_FILE", "r") as f:
    data = json.load(f)

if "$skill" not in data["skills"]:
    data["skills"]["$skill"] = {
        "total_uses": 0,
        "successful_uses": 0,
        "failures": 0,
        "last_used": None,
        "last_updated": None,
        "failure_history": []
    }

skill_data = data["skills"]["$skill"]

if "$metric" == "use":
    skill_data["total_uses"] += 1
    skill_data["last_used"] = datetime.now(timezone.utc).isoformat()
elif "$metric" == "success":
    skill_data["successful_uses"] += 1
elif "$metric" == "failure":
    skill_data["failures"] += 1
    skill_data["failure_history"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": "$value"
    })

# Calculate effectiveness
if skill_data["total_uses"] > 0:
    skill_data["effectiveness_rate"] = round(
        skill_data["successful_uses"] / skill_data["total_uses"], 3
    )

with open("$METRICS_FILE", "w") as f:
    json.dump(data, f, indent=2)

EOF
}

case "$COMMAND" in
    use)
        update_metrics "$SKILL" "use"
        echo "✓ Recorded use of '$SKILL'"
        ;;

    success)
        update_metrics "$SKILL" "success"
        echo "✓ Recorded successful outcome for '$SKILL'"
        ;;

    failure)
        [[ $# -lt 3 ]] && { echo "Error: failure reason required"; exit 1; }
        REASON="$3"
        update_metrics "$SKILL" "failure" "$REASON"
        echo "✗ Recorded failure for '$SKILL': $REASON"
        ;;

    stats)
        python3 - <<EOF
import json

with open("$METRICS_FILE", "r") as f:
    data = json.load(f)

if "$SKILL" not in data["skills"]:
    print(f"No data for skill: $SKILL")
    exit(1)

s = data["skills"]["$SKILL"]
print(f"\n{'='*50}")
print(f"Skill: $SKILL")
print(f"{'='*50}")
print(f"Total Uses:        {s['total_uses']}")
print(f"Successful Uses:   {s['successful_uses']}")
print(f"Failures:          {s['failures']}")
print(f"Effectiveness:     {s.get('effectiveness_rate', 0)*100:.1f}%")
print(f"Last Used:         {s.get('last_used', 'Never')}")
print(f"Last Updated:      {s.get('last_updated', 'Never')}")

if s['failure_history']:
    print(f"\nRecent Failures:")
    for f in s['failure_history'][-5:]:
        print(f"  - {f['timestamp']}: {f['reason']}")
print()
EOF
        ;;

    all-stats)
        python3 - <<EOF
import json

with open("$METRICS_FILE", "r") as f:
    data = json.load(f)

print(f"\n{'='*70}")
print(f"{'Skill':<30} {'Uses':<8} {'Success':<8} {'Failures':<8} {'Rate':<10}")
print(f"{'='*70}")

for skill, s in sorted(data["skills"].items()):
    rate = s.get('effectiveness_rate', 0) * 100
    print(f"{skill:<30} {s['total_uses']:<8} {s['successful_uses']:<8} {s['failures']:<8} {rate:<10.1f}%")

print(f"{'='*70}\n")
EOF
        ;;

    *)
        echo "Error: Unknown command: $COMMAND"
        usage
        ;;
esac
