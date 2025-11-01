#!/usr/bin/env python3
"""
Comprehensive MCP Server Testing Script
Tests the Hostaway MCP Server at http://localhost:8000
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk"
HOSTAWAY_ACCOUNT_ID = os.getenv("HOSTAWAY_ACCOUNT_ID")
HOSTAWAY_SECRET_KEY = os.getenv("HOSTAWAY_SECRET_KEY")

# Test results storage
TEST_RESULTS_DIR = Path(f"/tmp/mcp_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Test counters
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": [],
}


class Colors:
    """ANSI color codes"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text: str) -> None:
    """Print a section header"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_test(text: str) -> None:
    """Print a test description"""
    print(f"{Colors.YELLOW}TEST:{Colors.NC} {text}")
    test_results["total"] += 1


def print_pass(text: str) -> None:
    """Print a passing test"""
    print(f"{Colors.GREEN}✓ PASS:{Colors.NC} {text}")
    test_results["passed"] += 1


def print_fail(text: str) -> None:
    """Print a failing test"""
    print(f"{Colors.RED}✗ FAIL:{Colors.NC} {text}")
    test_results["failed"] += 1


def print_warning(text: str) -> None:
    """Print a warning"""
    print(f"{Colors.YELLOW}⚠ WARNING:{Colors.NC} {text}")
    test_results["warnings"] += 1


def print_info(text: str) -> None:
    """Print informational text"""
    print(f"{Colors.BLUE}ℹ INFO:{Colors.NC} {text}")


def save_response(filename: str, data: Any) -> None:
    """Save response data to a file"""
    filepath = TEST_RESULTS_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def test_phase_1_health() -> dict[str, Any]:
    """Phase 1: Server Health & Connectivity"""
    print_header("PHASE 1: Server Health & Connectivity")

    results = {}

    # Test 1.1: Health Endpoint
    print_test("1.1 - Health Endpoint Availability")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print_pass(f"Health endpoint returned 200 OK ({elapsed:.3f}s)")
            data = response.json()
            save_response("health_response.json", data)

            if data.get("status") == "healthy":
                print_pass("Server status is healthy")
            else:
                print_fail(f"Server status is not healthy: {data.get('status')}")

            version = data.get("version")
            print_info(f"Server version: {version}")

            if elapsed < 1.0:
                print_pass("Response time is acceptable (<1s)")
            else:
                print_warning(f"Response time is slow ({elapsed:.3f}s)")

            results["health"] = {"status": "passed", "response_time": elapsed, "data": data}
        else:
            print_fail(f"Health endpoint returned {response.status_code} (expected 200)")
            results["health"] = {"status": "failed", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"Health endpoint request failed: {e}")
        results["health"] = {"status": "error", "error": str(e)}

    # Test 1.2: Root Endpoint
    print_test("1.2 - Root Endpoint Availability")
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=10.0)
        if response.status_code == 200:
            print_pass("Root endpoint returned 200 OK")
            data = response.json()
            save_response("root_response.json", data)

            mcp_endpoint = data.get("mcp_endpoint")
            if mcp_endpoint == "/mcp":
                print_pass(f"MCP endpoint path is correct: {mcp_endpoint}")
            else:
                print_fail(f"MCP endpoint path is incorrect: {mcp_endpoint}")

            results["root"] = {"status": "passed", "data": data}
        else:
            print_fail(f"Root endpoint returned {response.status_code} (expected 200)")
            results["root"] = {"status": "failed", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"Root endpoint request failed: {e}")
        results["root"] = {"status": "error", "error": str(e)}

    # Test 1.3: OpenAPI Documentation
    print_test("1.3 - OpenAPI Documentation Availability")
    try:
        response = httpx.get(f"{BASE_URL}/openapi.json", timeout=10.0)
        if response.status_code == 200:
            print_pass("OpenAPI spec is available")
            data = response.json()
            save_response("openapi_spec.json", data)

            endpoint_count = len(data.get("paths", {}))
            print_info(f"Total API endpoints: {endpoint_count}")

            results["openapi"] = {"status": "passed", "endpoint_count": endpoint_count}
        else:
            print_fail(f"OpenAPI spec returned {response.status_code} (expected 200)")
            results["openapi"] = {"status": "failed", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"OpenAPI spec request failed: {e}")
        results["openapi"] = {"status": "error", "error": str(e)}

    return results


def test_phase_2_authentication() -> dict[str, Any]:
    """Phase 2: Authentication Flow"""
    print_header("PHASE 2: Authentication Flow")

    results = {}

    # Test 2.1: Hostaway OAuth Authentication
    print_test("2.1 - Hostaway OAuth Authentication")
    try:
        auth_data = {"account_id": HOSTAWAY_ACCOUNT_ID, "secret_key": HOSTAWAY_SECRET_KEY}
        response = httpx.post(f"{BASE_URL}/auth/authenticate", json=auth_data, timeout=30.0)

        if response.status_code == 200:
            print_pass("Authentication successful")
            data = response.json()
            save_response("auth_response.json", data)

            access_token = data.get("access_token")
            expires_in = data.get("expires_in")
            print_info(f"Access token received (expires in {expires_in}s)")

            # Save token for subsequent tests
            (TEST_RESULTS_DIR / "access_token.txt").write_text(access_token)

            results["authentication"] = {
                "status": "passed",
                "expires_in": expires_in,
                "has_token": bool(access_token),
            }
        else:
            print_fail(f"Authentication failed with HTTP {response.status_code}")
            print_info(f"Response: {response.text}")
            results["authentication"] = {
                "status": "failed",
                "status_code": response.status_code,
            }

    except Exception as e:
        print_fail(f"Authentication request failed: {e}")
        results["authentication"] = {"status": "error", "error": str(e)}

    return results


def test_phase_3_listings(access_token: str) -> dict[str, Any]:
    """Phase 3: Property Listings Operations"""
    print_header("PHASE 3: Property Listings Operations")

    results = {}
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test 3.1: List All Properties
    print_test("3.1 - List All Properties")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/api/listings", headers=headers, timeout=30.0)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print_pass(f"Listings retrieved successfully ({elapsed:.3f}s)")
            data = response.json()
            save_response("listings_response.json", data)

            property_count = len(data.get("listings", []))
            print_info(f"Total properties returned: {property_count}")

            if property_count > 0:
                print_pass("Properties found in response")
                first_property_id = data["listings"][0]["id"]
                (TEST_RESULTS_DIR / "test_property_id.txt").write_text(str(first_property_id))
                print_info(f"Test property ID: {first_property_id}")
            else:
                print_warning("No properties found in account")

            if elapsed < 2.0:
                print_pass("Response time is acceptable (<2s)")
            else:
                print_warning(f"Response time is slow ({elapsed:.3f}s)")

            results["list_properties"] = {
                "status": "passed",
                "response_time": elapsed,
                "property_count": property_count,
            }
        else:
            print_fail(f"Listings retrieval failed with HTTP {response.status_code}")
            print_info(f"Response: {response.text}")
            results["list_properties"] = {
                "status": "failed",
                "status_code": response.status_code,
            }

    except Exception as e:
        print_fail(f"Listings request failed: {e}")
        results["list_properties"] = {"status": "error", "error": str(e)}

    # Test 3.2: Get Property Details
    property_id_file = TEST_RESULTS_DIR / "test_property_id.txt"
    if property_id_file.exists():
        property_id = property_id_file.read_text().strip()

        print_test("3.2 - Get Property Details")
        try:
            start_time = time.time()
            response = httpx.get(
                f"{BASE_URL}/api/listings/{property_id}",
                headers=headers,
                timeout=30.0,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                print_pass(f"Property details retrieved successfully ({elapsed:.3f}s)")
                data = response.json()
                save_response("property_details_response.json", data)

                returned_id = str(data.get("id"))
                if returned_id == str(property_id):
                    print_pass("Property ID matches requested ID")
                else:
                    print_fail(f"Property ID mismatch: expected {property_id}, got {returned_id}")

                results["property_details"] = {
                    "status": "passed",
                    "response_time": elapsed,
                }
            else:
                print_fail(f"Property details retrieval failed with HTTP {response.status_code}")
                results["property_details"] = {
                    "status": "failed",
                    "status_code": response.status_code,
                }

        except Exception as e:
            print_fail(f"Property details request failed: {e}")
            results["property_details"] = {"status": "error", "error": str(e)}

        # Test 3.3: Check Property Availability
        print_test("3.3 - Check Property Availability")
        try:
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

            start_time = time.time()
            response = httpx.get(
                f"{BASE_URL}/api/listings/{property_id}/calendar",
                headers=headers,
                params={"start_date": start_date, "end_date": end_date},
                timeout=30.0,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                print_pass(f"Availability retrieved successfully ({elapsed:.3f}s)")
                data = response.json()
                save_response("availability_response.json", data)

                available_days = len(
                    [d for d in data.get("days", []) if d.get("status") == "available"]
                )
                print_info(f"Available days in next 30 days: {available_days}")

                results["availability"] = {
                    "status": "passed",
                    "response_time": elapsed,
                    "available_days": available_days,
                }
            else:
                print_fail(f"Availability retrieval failed with HTTP {response.status_code}")
                results["availability"] = {
                    "status": "failed",
                    "status_code": response.status_code,
                }

        except Exception as e:
            print_fail(f"Availability request failed: {e}")
            results["availability"] = {"status": "error", "error": str(e)}

    else:
        print_warning("Skipping property details and availability tests (no property ID available)")

    return results


def test_phase_4_bookings(access_token: str) -> dict[str, Any]:
    """Phase 4: Booking Management Operations"""
    print_header("PHASE 4: Booking Management Operations")

    results = {}
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test 4.1: List Recent Reservations
    print_test("4.1 - List Recent Reservations")
    try:
        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/api/reservations",
            headers=headers,
            params={"limit": 10},
            timeout=30.0,
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print_pass(f"Reservations retrieved successfully ({elapsed:.3f}s)")
            data = response.json()
            save_response("reservations_response.json", data)

            reservation_count = len(data.get("reservations", []))
            print_info(f"Total reservations returned: {reservation_count}")

            if reservation_count > 0:
                print_pass("Reservations found in response")
                first_booking_id = data["reservations"][0]["id"]
                (TEST_RESULTS_DIR / "test_booking_id.txt").write_text(str(first_booking_id))
                print_info(f"Test booking ID: {first_booking_id}")
            else:
                print_warning("No reservations found in account")

            results["list_reservations"] = {
                "status": "passed",
                "response_time": elapsed,
                "reservation_count": reservation_count,
            }
        else:
            print_fail(f"Reservations retrieval failed with HTTP {response.status_code}")
            results["list_reservations"] = {
                "status": "failed",
                "status_code": response.status_code,
            }

    except Exception as e:
        print_fail(f"Reservations request failed: {e}")
        results["list_reservations"] = {"status": "error", "error": str(e)}

    # Test 4.2: Get Reservation Details
    booking_id_file = TEST_RESULTS_DIR / "test_booking_id.txt"
    if booking_id_file.exists():
        booking_id = booking_id_file.read_text().strip()

        print_test("4.2 - Get Reservation Details")
        try:
            start_time = time.time()
            response = httpx.get(
                f"{BASE_URL}/api/reservations/{booking_id}",
                headers=headers,
                timeout=30.0,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                print_pass(f"Booking details retrieved successfully ({elapsed:.3f}s)")
                data = response.json()
                save_response("booking_details_response.json", data)

                returned_id = str(data.get("id"))
                if returned_id == str(booking_id):
                    print_pass("Booking ID matches requested ID")
                else:
                    print_fail(f"Booking ID mismatch: expected {booking_id}, got {returned_id}")

                results["booking_details"] = {
                    "status": "passed",
                    "response_time": elapsed,
                }
            else:
                print_fail(f"Booking details retrieval failed with HTTP {response.status_code}")
                results["booking_details"] = {
                    "status": "failed",
                    "status_code": response.status_code,
                }

        except Exception as e:
            print_fail(f"Booking details request failed: {e}")
            results["booking_details"] = {"status": "error", "error": str(e)}

    else:
        print_warning("Skipping booking details test (no booking ID available)")

    return results


def test_phase_5_financial(access_token: str) -> dict[str, Any]:
    """Phase 5: Financial Reporting Operations"""
    print_header("PHASE 5: Financial Reporting Operations")

    results = {}
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test 5.1: Get Financial Analytics
    print_test("5.1 - Get Financial Analytics")
    try:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/api/analytics/financial",
            headers=headers,
            params={"start_date": start_date, "end_date": end_date},
            timeout=30.0,
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print_pass(f"Financial analytics retrieved successfully ({elapsed:.3f}s)")
            data = response.json()
            save_response("financial_analytics_response.json", data)

            total_revenue = data.get("total_revenue")
            avg_rate = data.get("average_rate")
            print_info(f"Total revenue: {total_revenue}")
            print_info(f"Average rate: {avg_rate}")

            results["financial_analytics"] = {
                "status": "passed",
                "response_time": elapsed,
                "total_revenue": total_revenue,
                "average_rate": avg_rate,
            }
        else:
            print_fail(f"Financial analytics retrieval failed with HTTP {response.status_code}")
            results["financial_analytics"] = {
                "status": "failed",
                "status_code": response.status_code,
            }

    except Exception as e:
        print_fail(f"Financial analytics request failed: {e}")
        results["financial_analytics"] = {"status": "error", "error": str(e)}

    return results


def test_phase_6_validation() -> dict[str, Any]:
    """Phase 6: Response Validation & Headers"""
    print_header("PHASE 6: Response Validation & Headers")

    results = {}

    # Test 6.1: Check Rate Limiting Headers
    print_test("6.1 - Check Rate Limiting Headers")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        rate_limit_headers = {k: v for k, v in response.headers.items() if "ratelimit" in k.lower()}

        if rate_limit_headers:
            print_pass("Rate limiting headers present")
            for key, value in rate_limit_headers.items():
                print_info(f"  {key}: {value}")
            results["rate_limit_headers"] = {"status": "passed", "headers": rate_limit_headers}
        else:
            print_warning("Rate limiting headers not found")
            results["rate_limit_headers"] = {"status": "warning"}

    except Exception as e:
        print_fail(f"Rate limit headers check failed: {e}")
        results["rate_limit_headers"] = {"status": "error", "error": str(e)}

    # Test 6.2: Check CORS Headers
    print_test("6.2 - Check CORS Headers")
    try:
        response = httpx.get(
            f"{BASE_URL}/health",
            headers={"Origin": "http://example.com"},
            timeout=10.0,
        )
        cors_headers = {k: v for k, v in response.headers.items() if "access-control" in k.lower()}

        if cors_headers:
            print_pass("CORS headers present")
            for key, value in cors_headers.items():
                print_info(f"  {key}: {value}")
            results["cors_headers"] = {"status": "passed", "headers": cors_headers}
        else:
            print_warning("CORS headers not found")
            results["cors_headers"] = {"status": "warning"}

    except Exception as e:
        print_fail(f"CORS headers check failed: {e}")
        results["cors_headers"] = {"status": "error", "error": str(e)}

    # Test 6.3: Check Response Content-Type
    print_test("6.3 - Check Response Content-Type")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            print_pass(f"Content-Type is application/json: {content_type}")
            results["content_type"] = {"status": "passed", "content_type": content_type}
        else:
            print_warning(f"Content-Type might not be correct: {content_type}")
            results["content_type"] = {"status": "warning", "content_type": content_type}

    except Exception as e:
        print_fail(f"Content-Type check failed: {e}")
        results["content_type"] = {"status": "error", "error": str(e)}

    return results


def test_phase_7_error_handling() -> dict[str, Any]:
    """Phase 7: Error Handling"""
    print_header("PHASE 7: Error Handling")

    results = {}

    # Test 7.1: Test 404 Not Found
    print_test("7.1 - Test 404 Not Found")
    try:
        response = httpx.get(f"{BASE_URL}/nonexistent/endpoint", timeout=10.0)
        if response.status_code == 404:
            print_pass("404 Not Found handled correctly")
            results["not_found"] = {"status": "passed"}
        else:
            print_fail(f"404 Not Found not handled correctly (got {response.status_code})")
            results["not_found"] = {"status": "failed", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"404 test failed: {e}")
        results["not_found"] = {"status": "error", "error": str(e)}

    # Test 7.2: Test Invalid JSON
    print_test("7.2 - Test Invalid JSON")
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/authenticate",
            content=b"{invalid json}",
            headers={"Content-Type": "application/json"},
            timeout=10.0,
        )
        if response.status_code in [400, 422]:
            print_pass(f"Invalid JSON handled correctly (HTTP {response.status_code})")
            results["invalid_json"] = {"status": "passed", "status_code": response.status_code}
        else:
            print_warning(f"Invalid JSON handling returned unexpected code: {response.status_code}")
            results["invalid_json"] = {"status": "warning", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"Invalid JSON test failed: {e}")
        results["invalid_json"] = {"status": "error", "error": str(e)}

    # Test 7.3: Test Missing Required Fields
    print_test("7.3 - Test Missing Required Fields")
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/authenticate",
            json={},
            timeout=10.0,
        )
        if response.status_code == 422:
            print_pass("Missing required fields handled correctly")
            results["missing_fields"] = {"status": "passed"}
        else:
            print_warning(
                f"Missing fields handling returned unexpected code: {response.status_code}"
            )
            results["missing_fields"] = {"status": "warning", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"Missing fields test failed: {e}")
        results["missing_fields"] = {"status": "error", "error": str(e)}

    # Test 7.4: Test Unauthorized Access
    print_test("7.4 - Test Unauthorized Access")
    try:
        response = httpx.get(f"{BASE_URL}/api/listings", timeout=10.0)
        if response.status_code in [401, 403]:
            print_pass(f"Unauthorized access handled correctly (HTTP {response.status_code})")
            results["unauthorized"] = {"status": "passed", "status_code": response.status_code}
        else:
            print_warning(f"Unauthorized access returned unexpected code: {response.status_code}")
            results["unauthorized"] = {"status": "warning", "status_code": response.status_code}

    except Exception as e:
        print_fail(f"Unauthorized access test failed: {e}")
        results["unauthorized"] = {"status": "error", "error": str(e)}

    return results


def test_phase_8_performance() -> dict[str, Any]:
    """Phase 8: Performance Metrics"""
    print_header("PHASE 8: Performance Metrics")

    results = {}

    # Test 8.1: Measure Health Endpoint Performance
    print_test("8.1 - Measure Health Endpoint Performance")
    try:
        times = []
        for _ in range(10):
            start_time = time.time()
            response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
            elapsed = time.time() - start_time
            if response.status_code == 200:
                times.append(elapsed)

        avg_time = sum(times) / len(times)
        print_info(f"Average response time (10 requests): {avg_time:.3f}s")

        if avg_time < 0.5:
            print_pass("Average response time is excellent (<0.5s)")
        elif avg_time < 1.0:
            print_pass("Average response time is good (<1.0s)")
        else:
            print_warning(f"Average response time is slow ({avg_time:.3f}s)")

        results["performance"] = {
            "status": "passed",
            "avg_response_time": avg_time,
            "sample_size": len(times),
        }

    except Exception as e:
        print_fail(f"Performance test failed: {e}")
        results["performance"] = {"status": "error", "error": str(e)}

    return results


def generate_report() -> None:
    """Generate final test report"""
    print_header("TEST SUMMARY")

    print(f"Total Tests:     {test_results['total']}")
    print(f"{Colors.GREEN}Passed:          {test_results['passed']}{Colors.NC}")
    print(f"{Colors.RED}Failed:          {test_results['failed']}{Colors.NC}")
    print(f"{Colors.YELLOW}Warnings:        {test_results['warnings']}{Colors.NC}")

    if test_results["total"] > 0:
        pass_rate = (test_results["passed"] / test_results["total"]) * 100
        print(f"\nPass Rate:       {pass_rate:.2f}%")

    if test_results["failed"] == 0:
        print(f"\n{Colors.GREEN}✓ ALL TESTS PASSED{Colors.NC}")
        exit_code = 0
    else:
        print(f"\n{Colors.RED}✗ SOME TESTS FAILED{Colors.NC}")
        exit_code = 1

    print_info(f"Detailed results saved to: {TEST_RESULTS_DIR}")

    # Generate JSON summary
    summary = {
        "test_date": datetime.now().isoformat(),
        "server_url": BASE_URL,
        "total_tests": test_results["total"],
        "passed": test_results["passed"],
        "failed": test_results["failed"],
        "warnings": test_results["warnings"],
        "pass_rate": pass_rate if test_results["total"] > 0 else 0,
        "exit_code": exit_code,
        "tests": test_results["tests"],
    }

    save_response("test_summary.json", summary)
    print_info(f"JSON summary saved to: {TEST_RESULTS_DIR}/test_summary.json")

    return exit_code


def main() -> int:
    """Main test execution"""
    print_header("Hostaway MCP Server - Comprehensive Test Report")
    print_info(f"Test Results Directory: {TEST_RESULTS_DIR}")
    print_info(f"Server: {BASE_URL}")
    print_info(f"Test Date: {datetime.now().isoformat()}")

    # Phase 1: Health & Connectivity
    phase1_results = test_phase_1_health()
    test_results["tests"].append({"phase": 1, "results": phase1_results})

    # Phase 2: Authentication
    phase2_results = test_phase_2_authentication()
    test_results["tests"].append({"phase": 2, "results": phase2_results})

    # Get access token for subsequent tests
    access_token_file = TEST_RESULTS_DIR / "access_token.txt"
    if access_token_file.exists():
        access_token = access_token_file.read_text().strip()

        # Phase 3: Property Listings
        phase3_results = test_phase_3_listings(access_token)
        test_results["tests"].append({"phase": 3, "results": phase3_results})

        # Phase 4: Booking Management
        phase4_results = test_phase_4_bookings(access_token)
        test_results["tests"].append({"phase": 4, "results": phase4_results})

        # Phase 5: Financial Reporting
        phase5_results = test_phase_5_financial(access_token)
        test_results["tests"].append({"phase": 5, "results": phase5_results})
    else:
        print_warning("Skipping phases 3-5 (no access token available)")

    # Phase 6: Response Validation
    phase6_results = test_phase_6_validation()
    test_results["tests"].append({"phase": 6, "results": phase6_results})

    # Phase 7: Error Handling
    phase7_results = test_phase_7_error_handling()
    test_results["tests"].append({"phase": 7, "results": phase7_results})

    # Phase 8: Performance
    phase8_results = test_phase_8_performance()
    test_results["tests"].append({"phase": 8, "results": phase8_results})

    # Generate final report
    exit_code = generate_report()

    return exit_code


if __name__ == "__main__":
    exit(main())
