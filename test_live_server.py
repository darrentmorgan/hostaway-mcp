#!/usr/bin/env python3
"""Comprehensive live server testing script for Hostaway MCP Server.

Tests the running server at http://localhost:8000 without authentication.
Validates public endpoints, error handling, response formats, and performance.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import httpx


class Colors:
    """Terminal colors for output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestResult:
    """Container for test results."""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details: list[dict[str, Any]] = []

    def add_pass(self, detail: str, data: dict[str, Any] | None = None):
        self.passed += 1
        self.details.append({"status": "PASS", "detail": detail, "data": data})

    def add_fail(self, detail: str, data: dict[str, Any] | None = None):
        self.failed += 1
        self.details.append({"status": "FAIL", "detail": detail, "data": data})

    def add_warning(self, detail: str, data: dict[str, Any] | None = None):
        self.warnings += 1
        self.details.append({"status": "WARN", "detail": detail, "data": data})


class ServerTester:
    """Comprehensive server testing class."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)
        self.results: dict[str, TestResult] = {}

    def print_header(self, title: str):
        """Print test section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

    def print_result(self, status: str, message: str):
        """Print test result with color."""
        if status == "PASS":
            print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")
        elif status == "FAIL":
            print(f"  {Colors.RED}✗{Colors.RESET} {message}")
        elif status == "WARN":
            print(f"  {Colors.YELLOW}!{Colors.RESET} {message}")
        else:
            print(f"  {message}")

    def test_health_check(self) -> TestResult:
        """Test /health endpoint."""
        result = TestResult("Health Check")
        self.print_header("1. Health Check Testing")

        try:
            start_time = time.time()
            response = self.client.get(f"{self.base_url}/health")
            response_time = (time.time() - start_time) * 1000

            # Test HTTP status
            if response.status_code == 200:
                result.add_pass(f"HTTP 200 OK (Response time: {response_time:.2f}ms)")
                self.print_result(
                    "PASS", f"Health endpoint responds with 200 OK ({response_time:.2f}ms)"
                )
            else:
                result.add_fail(f"Expected HTTP 200, got {response.status_code}")
                self.print_result("FAIL", f"Expected HTTP 200, got {response.status_code}")
                return result

            # Test response is valid JSON
            try:
                data = response.json()
                result.add_pass("Valid JSON response")
                self.print_result("PASS", "Response is valid JSON")
            except json.JSONDecodeError as e:
                result.add_fail(f"Invalid JSON: {e}")
                self.print_result("FAIL", f"Invalid JSON: {e}")
                return result

            # Test required fields
            required_fields = ["status", "timestamp", "version", "service"]
            for field in required_fields:
                if field in data:
                    result.add_pass(f"Field '{field}' present: {data[field]}")
                    self.print_result("PASS", f"Field '{field}' present: {data[field]}")
                else:
                    result.add_fail(f"Missing required field: {field}")
                    self.print_result("FAIL", f"Missing required field: {field}")

            # Test context_protection metrics
            if "context_protection" in data:
                metrics = data["context_protection"]
                result.add_pass(f"Context protection metrics present: {metrics}")
                self.print_result(
                    "PASS", f"Context protection metrics present with {len(metrics)} fields"
                )

                # Validate uptime
                if "uptime_seconds" in metrics:
                    uptime_hours = metrics["uptime_seconds"] / 3600
                    result.add_pass(f"Server uptime: {uptime_hours:.2f} hours")
                    self.print_result("PASS", f"Server uptime: {uptime_hours:.2f} hours")
            else:
                result.add_warning("No context_protection metrics found")
                self.print_result("WARN", "No context_protection metrics found")

            # Test response time
            if response_time < 500:
                result.add_pass(f"Fast response time: {response_time:.2f}ms")
                self.print_result("PASS", f"Fast response time: {response_time:.2f}ms")
            elif response_time < 2000:
                result.add_warning(f"Acceptable response time: {response_time:.2f}ms")
                self.print_result("WARN", f"Acceptable response time: {response_time:.2f}ms")
            else:
                result.add_fail(f"Slow response time: {response_time:.2f}ms")
                self.print_result("FAIL", f"Slow response time: {response_time:.2f}ms")

        except httpx.RequestError as e:
            result.add_fail(f"Request error: {e}")
            self.print_result("FAIL", f"Request error: {e}")
        except Exception as e:
            result.add_fail(f"Unexpected error: {e}")
            self.print_result("FAIL", f"Unexpected error: {e}")

        return result

    def test_root_endpoint(self) -> TestResult:
        """Test root / endpoint."""
        result = TestResult("Root Endpoint")
        self.print_header("2. Root Endpoint Testing")

        try:
            response = self.client.get(f"{self.base_url}/")

            if response.status_code == 200:
                result.add_pass("Root endpoint responds with 200 OK")
                self.print_result("PASS", "Root endpoint responds with 200 OK")

                data = response.json()
                expected_fields = ["service", "version", "mcp_endpoint", "docs"]
                for field in expected_fields:
                    if field in data:
                        result.add_pass(f"Field '{field}': {data[field]}")
                        self.print_result("PASS", f"Field '{field}': {data[field]}")
                    else:
                        result.add_warning(f"Missing field: {field}")
                        self.print_result("WARN", f"Missing field: {field}")
            else:
                result.add_fail(f"Expected 200, got {response.status_code}")
                self.print_result("FAIL", f"Expected 200, got {response.status_code}")

        except Exception as e:
            result.add_fail(f"Error: {e}")
            self.print_result("FAIL", f"Error: {e}")

        return result

    def test_openapi_spec(self) -> TestResult:
        """Test OpenAPI specification endpoint."""
        result = TestResult("OpenAPI Specification")
        self.print_header("3. OpenAPI Specification Testing")

        try:
            response = self.client.get(f"{self.base_url}/openapi.json")

            if response.status_code == 200:
                result.add_pass("OpenAPI spec available")
                self.print_result("PASS", "OpenAPI spec available at /openapi.json")

                spec = response.json()

                # Validate OpenAPI version
                if "openapi" in spec:
                    result.add_pass(f"OpenAPI version: {spec['openapi']}")
                    self.print_result("PASS", f"OpenAPI version: {spec['openapi']}")
                else:
                    result.add_fail("Missing OpenAPI version field")
                    self.print_result("FAIL", "Missing OpenAPI version field")

                # Validate info
                if "info" in spec:
                    info = spec["info"]
                    result.add_pass(f"API title: {info.get('title')}")
                    result.add_pass(f"API version: {info.get('version')}")
                    self.print_result("PASS", f"API: {info.get('title')} v{info.get('version')}")

                # Count endpoints
                if "paths" in spec:
                    endpoint_count = len(spec["paths"])
                    result.add_pass(f"Documented endpoints: {endpoint_count}")
                    self.print_result("PASS", f"Total documented endpoints: {endpoint_count}")

                    # List all endpoints
                    print(f"\n  {Colors.BOLD}Documented Endpoints:{Colors.RESET}")
                    for path, methods in sorted(spec["paths"].items()):
                        for method in methods.keys():
                            summary = methods[method].get("summary", "No summary")
                            print(f"    {method.upper():6} {path:45} - {summary}")
                else:
                    result.add_fail("No paths defined in OpenAPI spec")
                    self.print_result("FAIL", "No paths defined in OpenAPI spec")

            else:
                result.add_fail(f"Expected 200, got {response.status_code}")
                self.print_result("FAIL", f"Expected 200, got {response.status_code}")

        except Exception as e:
            result.add_fail(f"Error: {e}")
            self.print_result("FAIL", f"Error: {e}")

        return result

    def test_swagger_ui(self) -> TestResult:
        """Test Swagger UI documentation."""
        result = TestResult("Swagger UI")
        self.print_header("4. Swagger UI Testing")

        try:
            response = self.client.get(f"{self.base_url}/docs")

            if response.status_code == 200:
                result.add_pass("Swagger UI available at /docs")
                self.print_result("PASS", "Swagger UI available at /docs")

                # Check if response looks like HTML
                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type:
                    result.add_pass(f"Correct content type: {content_type}")
                    self.print_result("PASS", f"Content-Type: {content_type}")
                else:
                    result.add_warning(f"Unexpected content type: {content_type}")
                    self.print_result("WARN", f"Unexpected content type: {content_type}")
            else:
                result.add_fail(f"Expected 200, got {response.status_code}")
                self.print_result("FAIL", f"Expected 200, got {response.status_code}")

        except Exception as e:
            result.add_fail(f"Error: {e}")
            self.print_result("FAIL", f"Error: {e}")

        return result

    def test_error_handling(self) -> TestResult:
        """Test error handling for invalid endpoints."""
        result = TestResult("Error Handling")
        self.print_header("5. Error Handling Testing")

        # Test 404 handling
        try:
            response = self.client.get(f"{self.base_url}/invalid-endpoint-12345")

            if response.status_code == 404:
                result.add_pass("404 error returned for invalid endpoint")
                self.print_result("PASS", "404 error returned for invalid endpoint")

                data = response.json()
                if "detail" in data:
                    result.add_pass(f"Error message present: {data['detail']}")
                    self.print_result("PASS", f"Error detail: {data['detail']}")
            else:
                result.add_fail(f"Expected 404, got {response.status_code}")
                self.print_result("FAIL", f"Expected 404, got {response.status_code}")

        except Exception as e:
            result.add_fail(f"Error testing 404: {e}")
            self.print_result("FAIL", f"Error testing 404: {e}")

        # Test 422 validation error
        try:
            response = self.client.post(
                f"{self.base_url}/auth/authenticate",
                json={"invalid": "data"},
            )

            if response.status_code == 422:
                result.add_pass("422 validation error for invalid request body")
                self.print_result("PASS", "422 validation error for invalid request body")

                data = response.json()
                if "detail" in data:
                    result.add_pass("Validation error details present")
                    self.print_result(
                        "PASS", f"Validation error details: {len(data['detail'])} error(s)"
                    )
            else:
                result.add_warning(f"Expected 422, got {response.status_code}")
                self.print_result("WARN", f"Expected 422, got {response.status_code}")

        except Exception as e:
            result.add_fail(f"Error testing validation: {e}")
            self.print_result("FAIL", f"Error testing validation: {e}")

        return result

    def test_authentication_required(self) -> TestResult:
        """Test that protected endpoints require authentication."""
        result = TestResult("Authentication Required")
        self.print_header("6. Authentication Testing")

        protected_endpoints = [
            ("/api/listings", "GET"),
            ("/api/reservations", "GET"),
            ("/api/financialReports", "GET"),
            ("/mcp", "GET"),
        ]

        for endpoint, method in protected_endpoints:
            try:
                if method == "GET":
                    response = self.client.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.client.request(method, f"{self.base_url}{endpoint}")

                if response.status_code == 401:
                    result.add_pass(f"{method} {endpoint} requires authentication (401)")
                    self.print_result("PASS", f"{method} {endpoint} requires authentication (401)")

                    data = response.json()
                    if "detail" in data and "API key" in data["detail"]:
                        result.add_pass(f"Appropriate error message: {data['detail']}")
                        self.print_result("PASS", f"Error message: {data['detail']}")
                else:
                    result.add_warning(
                        f"{method} {endpoint} returned {response.status_code} instead of 401"
                    )
                    self.print_result(
                        "WARN", f"{method} {endpoint} returned {response.status_code}"
                    )

            except Exception as e:
                result.add_fail(f"Error testing {endpoint}: {e}")
                self.print_result("FAIL", f"Error testing {endpoint}: {e}")

        return result

    def test_performance(self) -> TestResult:
        """Test server performance with multiple requests."""
        result = TestResult("Performance")
        self.print_header("7. Performance Testing")

        num_requests = 10
        response_times = []

        print(f"  Running {num_requests} requests to /health endpoint...\n")

        for i in range(num_requests):
            try:
                start_time = time.time()
                response = self.client.get(f"{self.base_url}/health")
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    response_times.append(response_time)
                    print(f"    Request {i + 1}/{num_requests}: {response_time:.2f}ms")

            except Exception as e:
                result.add_fail(f"Request {i + 1} failed: {e}")

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            result.add_pass(f"Average response time: {avg_time:.2f}ms")
            result.add_pass(f"Min response time: {min_time:.2f}ms")
            result.add_pass(f"Max response time: {max_time:.2f}ms")

            print(f"\n  {Colors.BOLD}Performance Summary:{Colors.RESET}")
            self.print_result("PASS", f"Average: {avg_time:.2f}ms")
            self.print_result("PASS", f"Min: {min_time:.2f}ms")
            self.print_result("PASS", f"Max: {max_time:.2f}ms")

            if avg_time < 500:
                result.add_pass("Excellent average response time (<500ms)")
                self.print_result("PASS", "Performance: Excellent (<500ms)")
            elif avg_time < 1000:
                result.add_pass("Good average response time (<1000ms)")
                self.print_result("PASS", "Performance: Good (<1000ms)")
            else:
                result.add_warning(f"Slow average response time: {avg_time:.2f}ms")
                self.print_result("WARN", f"Performance: Could be improved ({avg_time:.2f}ms)")

        return result

    def print_summary(self):
        """Print overall test summary."""
        self.print_header("TEST SUMMARY")

        total_passed = 0
        total_failed = 0
        total_warnings = 0

        print(f"  {Colors.BOLD}Results by Test Category:{Colors.RESET}\n")
        for name, result in self.results.items():
            total_passed += result.passed
            total_failed += result.failed
            total_warnings += result.warnings

            status_color = Colors.GREEN if result.failed == 0 else Colors.RED
            print(
                f"  {status_color}{name:30}{Colors.RESET} "
                f"Pass: {Colors.GREEN}{result.passed:2}{Colors.RESET} | "
                f"Fail: {Colors.RED}{result.failed:2}{Colors.RESET} | "
                f"Warn: {Colors.YELLOW}{result.warnings:2}{Colors.RESET}"
            )

        print(f"\n  {Colors.BOLD}Overall Totals:{Colors.RESET}")
        print(f"    {Colors.GREEN}Passed:  {total_passed}{Colors.RESET}")
        print(f"    {Colors.RED}Failed:  {total_failed}{Colors.RESET}")
        print(f"    {Colors.YELLOW}Warnings: {total_warnings}{Colors.RESET}")

        # Overall status
        if total_failed == 0:
            print(f"\n  {Colors.BOLD}{Colors.GREEN}✓ ALL TESTS PASSED{Colors.RESET}")
            print(f"  {Colors.GREEN}Server is healthy and ready for use{Colors.RESET}\n")
            return 0
        print(f"\n  {Colors.BOLD}{Colors.RED}✗ SOME TESTS FAILED{Colors.RESET}")
        print(f"  {Colors.RED}Server has issues that need attention{Colors.RESET}\n")
        return 1

    def run_all_tests(self) -> int:
        """Run all tests and return exit code."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Hostaway MCP Server - Live Testing Suite{Colors.RESET}")
        print(f"{Colors.BLUE}Target: {self.base_url}{Colors.RESET}")
        print(f"{Colors.BLUE}Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

        # Run all test suites
        self.results["Health Check"] = self.test_health_check()
        self.results["Root Endpoint"] = self.test_root_endpoint()
        self.results["OpenAPI Specification"] = self.test_openapi_spec()
        self.results["Swagger UI"] = self.test_swagger_ui()
        self.results["Error Handling"] = self.test_error_handling()
        self.results["Authentication"] = self.test_authentication_required()
        self.results["Performance"] = self.test_performance()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    tester = ServerTester(base_url)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
