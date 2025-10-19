"""Test coverage report generator for financial endpoints.

Runs comprehensive tests and generates coverage analysis.
"""

import subprocess
import sys
from pathlib import Path


def run_financial_tests() -> tuple[int, str]:
    """Run financial endpoint tests with coverage.

    Returns:
        Tuple of (exit_code, output)
    """
    # Run pytest with coverage for financial endpoints
    cmd = [
        "pytest",
        "tests/unit/test_financial_errors.py",
        "tests/integration/test_financial_api.py",
        "-v",
        "--tb=short",
        "--cov=src/api/routes/financial",
        "--cov=src/services/hostaway_client",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/financial",
        "--cov-report=json:coverage_financial.json",
    ]

    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    return result.returncode, result.stdout + result.stderr


def analyze_coverage(json_path: Path) -> dict:
    """Analyze coverage JSON report.

    Args:
        json_path: Path to coverage JSON file

    Returns:
        Coverage analysis dict
    """
    import json

    if not json_path.exists():
        return {"error": "Coverage report not found"}

    with json_path.open() as f:
        data = json.load(f)

    totals = data.get("totals", {})

    return {
        "line_coverage": totals.get("percent_covered", 0),
        "lines_covered": totals.get("covered_lines", 0),
        "lines_total": totals.get("num_statements", 0),
        "missing_lines": totals.get("missing_lines", 0),
        "files": {
            path: {
                "coverage": info["summary"]["percent_covered"],
                "missing": info["summary"]["missing_lines"],
            }
            for path, info in data.get("files", {}).items()
        },
    }


def main() -> int:
    """Run tests and generate coverage report.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("=" * 80)
    print("Running Financial Endpoint Test Coverage Analysis")
    print("=" * 80)
    print()

    # Run tests
    exit_code, output = run_financial_tests()

    print(output)
    print()

    # Analyze coverage if tests passed
    if exit_code == 0:
        print("=" * 80)
        print("Coverage Analysis")
        print("=" * 80)
        print()

        json_path = Path(__file__).parent.parent / "coverage_financial.json"
        analysis = analyze_coverage(json_path)

        if "error" in analysis:
            print(f"Error: {analysis['error']}")
        else:
            print(f"Overall Line Coverage: {analysis['line_coverage']:.2f}%")
            print(f"Lines Covered: {analysis['lines_covered']}/{analysis['lines_total']}")
            print()

            print("File Coverage:")
            for file_path, file_data in analysis["files"].items():
                print(f"  {file_path}")
                print(f"    Coverage: {file_data['coverage']:.2f}%")
                print(f"    Missing Lines: {file_data['missing']}")
            print()

            # Check if coverage meets threshold
            threshold = 80.0
            if analysis["line_coverage"] >= threshold:
                print(f"✓ Coverage meets threshold ({threshold}%)")
            else:
                print(f"✗ Coverage below threshold ({threshold}%)")
                print(f"  Need to improve by: {threshold - analysis['line_coverage']:.2f}%")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
