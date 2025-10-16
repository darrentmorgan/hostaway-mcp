#!/bin/bash
# Quick secret scanning script

echo "Running secret scan..."

# Check for common secret patterns
patterns=(
    "password.*=.*['\"].*['\"]"
    "api[_-]?key.*=.*['\"].*['\"]"
    "secret.*=.*['\"].*['\"]"
    "token.*=.*['\"].*['\"]"
    "Bearer [A-Za-z0-9+/=]{20,}"
    "Basic [A-Za-z0-9+/=]{20,}"
)

found_issues=0
for pattern in "${patterns[@]}"; do
    results=$(grep -r -i "$pattern" --include="*.py" --include="*.ts" --include="*.js" --include="*.sh" --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir=".venv" . 2>/dev/null || true)
    if [ -n "$results" ]; then
        echo "Found potential secrets matching pattern: $pattern"
        echo "$results"
        found_issues=1
    fi
done

if [ $found_issues -eq 0 ]; then
    echo "No obvious secrets found in code files"
else
    echo "WARNING: Potential secrets found. Please review and remove them."
fi
