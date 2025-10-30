#!/bin/bash
# Comprehensive MCP Server Testing Script
# Testing Hostaway MCP Server at http://localhost:8000

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Server configuration
BASE_URL="http://localhost:8000"
API_KEY="mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk"

# Load Hostaway credentials from .env
export $(grep -v '^#' .env | xargs)

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
    ((TOTAL_TESTS++))
}

print_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAILED_TESTS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

# Test result storage
TEST_RESULTS_DIR="/tmp/mcp_test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_RESULTS_DIR"

print_header "Hostaway MCP Server - Comprehensive Test Report"
print_info "Test Results Directory: $TEST_RESULTS_DIR"
print_info "Server: $BASE_URL"
print_info "Test Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# ============================================================================
# PHASE 1: Server Health & Connectivity
# ============================================================================
print_header "PHASE 1: Server Health & Connectivity"

print_test "1.1 - Health Endpoint Availability"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" "$BASE_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -2 | head -1)
RESPONSE_TIME=$(echo "$HEALTH_RESPONSE" | tail -1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_pass "Health endpoint returned 200 OK (${RESPONSE_TIME}s)"
    echo "$HEALTH_BODY" | jq '.' > "$TEST_RESULTS_DIR/health_response.json"

    # Check health status
    STATUS=$(echo "$HEALTH_BODY" | jq -r '.status')
    if [ "$STATUS" = "healthy" ]; then
        print_pass "Server status is healthy"
    else
        print_fail "Server status is not healthy: $STATUS"
    fi

    # Check version
    VERSION=$(echo "$HEALTH_BODY" | jq -r '.version')
    print_info "Server version: $VERSION"

    # Check response time
    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
        print_pass "Response time is acceptable (<1s)"
    else
        print_warning "Response time is slow (${RESPONSE_TIME}s)"
    fi
else
    print_fail "Health endpoint returned $HTTP_CODE (expected 200)"
fi

print_test "1.2 - Root Endpoint Availability"
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/")
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -1)
ROOT_BODY=$(echo "$ROOT_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_pass "Root endpoint returned 200 OK"
    echo "$ROOT_BODY" | jq '.' > "$TEST_RESULTS_DIR/root_response.json"

    # Verify expected fields
    MCP_ENDPOINT=$(echo "$ROOT_BODY" | jq -r '.mcp_endpoint')
    if [ "$MCP_ENDPOINT" = "/mcp" ]; then
        print_pass "MCP endpoint path is correct: $MCP_ENDPOINT"
    else
        print_fail "MCP endpoint path is incorrect: $MCP_ENDPOINT"
    fi
else
    print_fail "Root endpoint returned $HTTP_CODE (expected 200)"
fi

print_test "1.3 - OpenAPI Documentation Availability"
OPENAPI_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/openapi.json")
HTTP_CODE=$(echo "$OPENAPI_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_pass "OpenAPI spec is available"
    echo "$OPENAPI_RESPONSE" | head -n -1 | jq '.' > "$TEST_RESULTS_DIR/openapi_spec.json"

    # Count available endpoints
    ENDPOINT_COUNT=$(echo "$OPENAPI_RESPONSE" | head -n -1 | jq '.paths | keys | length')
    print_info "Total API endpoints: $ENDPOINT_COUNT"
else
    print_fail "OpenAPI spec returned $HTTP_CODE (expected 200)"
fi

# ============================================================================
# PHASE 2: Authentication Flow
# ============================================================================
print_header "PHASE 2: Authentication Flow"

print_test "2.1 - Hostaway OAuth Authentication"
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"account_id\": \"$HOSTAWAY_ACCOUNT_ID\", \"secret_key\": \"$HOSTAWAY_SECRET_KEY\"}" \
    "$BASE_URL/auth/authenticate")
HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -1)
AUTH_BODY=$(echo "$AUTH_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_pass "Authentication successful"
    echo "$AUTH_BODY" | jq '.' > "$TEST_RESULTS_DIR/auth_response.json"

    # Extract and store access token
    ACCESS_TOKEN=$(echo "$AUTH_BODY" | jq -r '.access_token')
    EXPIRES_IN=$(echo "$AUTH_BODY" | jq -r '.expires_in')
    print_info "Access token received (expires in ${EXPIRES_IN}s)"

    # Save token for subsequent tests
    echo "$ACCESS_TOKEN" > "$TEST_RESULTS_DIR/access_token.txt"
else
    print_fail "Authentication failed with HTTP $HTTP_CODE"
    echo "$AUTH_BODY" | jq '.'
fi

# ============================================================================
# PHASE 3: Property Listings Operations
# ============================================================================
print_header "PHASE 3: Property Listings Operations"

if [ -f "$TEST_RESULTS_DIR/access_token.txt" ]; then
    ACCESS_TOKEN=$(cat "$TEST_RESULTS_DIR/access_token.txt")

    print_test "3.1 - List All Properties"
    LISTINGS_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/listings")
    HTTP_CODE=$(echo "$LISTINGS_RESPONSE" | tail -2 | head -1)
    RESPONSE_TIME=$(echo "$LISTINGS_RESPONSE" | tail -1)
    LISTINGS_BODY=$(echo "$LISTINGS_RESPONSE" | head -1)

    if [ "$HTTP_CODE" = "200" ]; then
        print_pass "Listings retrieved successfully (${RESPONSE_TIME}s)"
        echo "$LISTINGS_BODY" | jq '.' > "$TEST_RESULTS_DIR/listings_response.json"

        # Count properties
        PROPERTY_COUNT=$(echo "$LISTINGS_BODY" | jq '.listings | length')
        print_info "Total properties returned: $PROPERTY_COUNT"

        # Check if properties exist
        if [ "$PROPERTY_COUNT" -gt 0 ]; then
            print_pass "Properties found in response"

            # Extract first property ID for detail test
            FIRST_PROPERTY_ID=$(echo "$LISTINGS_BODY" | jq -r '.listings[0].id')
            echo "$FIRST_PROPERTY_ID" > "$TEST_RESULTS_DIR/test_property_id.txt"
            print_info "Test property ID: $FIRST_PROPERTY_ID"
        else
            print_warning "No properties found in account"
        fi

        # Check response time
        if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
            print_pass "Response time is acceptable (<2s)"
        else
            print_warning "Response time is slow (${RESPONSE_TIME}s)"
        fi
    else
        print_fail "Listings retrieval failed with HTTP $HTTP_CODE"
        echo "$LISTINGS_BODY"
    fi

    print_test "3.2 - Get Property Details"
    if [ -f "$TEST_RESULTS_DIR/test_property_id.txt" ]; then
        PROPERTY_ID=$(cat "$TEST_RESULTS_DIR/test_property_id.txt")

        DETAILS_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$BASE_URL/api/listings/$PROPERTY_ID")
        HTTP_CODE=$(echo "$DETAILS_RESPONSE" | tail -2 | head -1)
        RESPONSE_TIME=$(echo "$DETAILS_RESPONSE" | tail -1)
        DETAILS_BODY=$(echo "$DETAILS_RESPONSE" | head -1)

        if [ "$HTTP_CODE" = "200" ]; then
            print_pass "Property details retrieved successfully (${RESPONSE_TIME}s)"
            echo "$DETAILS_BODY" | jq '.' > "$TEST_RESULTS_DIR/property_details_response.json"

            # Verify property ID matches
            RETURNED_ID=$(echo "$DETAILS_BODY" | jq -r '.id')
            if [ "$RETURNED_ID" = "$PROPERTY_ID" ]; then
                print_pass "Property ID matches requested ID"
            else
                print_fail "Property ID mismatch: expected $PROPERTY_ID, got $RETURNED_ID"
            fi
        else
            print_fail "Property details retrieval failed with HTTP $HTTP_CODE"
            echo "$DETAILS_BODY"
        fi
    else
        print_warning "Skipping property details test (no property ID available)"
    fi

    print_test "3.3 - Check Property Availability"
    if [ -f "$TEST_RESULTS_DIR/test_property_id.txt" ]; then
        PROPERTY_ID=$(cat "$TEST_RESULTS_DIR/test_property_id.txt")

        # Get availability for next 30 days
        START_DATE=$(date -u +"%Y-%m-%d")
        END_DATE=$(date -u -v+30d +"%Y-%m-%d" 2>/dev/null || date -u -d "+30 days" +"%Y-%m-%d")

        AVAILABILITY_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$BASE_URL/api/listings/$PROPERTY_ID/calendar?start_date=$START_DATE&end_date=$END_DATE")
        HTTP_CODE=$(echo "$AVAILABILITY_RESPONSE" | tail -2 | head -1)
        RESPONSE_TIME=$(echo "$AVAILABILITY_RESPONSE" | tail -1)
        AVAILABILITY_BODY=$(echo "$AVAILABILITY_RESPONSE" | head -1)

        if [ "$HTTP_CODE" = "200" ]; then
            print_pass "Availability retrieved successfully (${RESPONSE_TIME}s)"
            echo "$AVAILABILITY_BODY" | jq '.' > "$TEST_RESULTS_DIR/availability_response.json"

            # Count available days
            AVAILABLE_DAYS=$(echo "$AVAILABILITY_BODY" | jq '[.days[] | select(.status == "available")] | length')
            print_info "Available days in next 30 days: $AVAILABLE_DAYS"
        else
            print_fail "Availability retrieval failed with HTTP $HTTP_CODE"
            echo "$AVAILABILITY_BODY"
        fi
    else
        print_warning "Skipping availability test (no property ID available)"
    fi

else
    print_warning "Skipping listings tests (no access token available)"
fi

# ============================================================================
# PHASE 4: Booking Management Operations
# ============================================================================
print_header "PHASE 4: Booking Management Operations"

if [ -f "$TEST_RESULTS_DIR/access_token.txt" ]; then
    ACCESS_TOKEN=$(cat "$TEST_RESULTS_DIR/access_token.txt")

    print_test "4.1 - List Recent Reservations"
    RESERVATIONS_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/reservations?limit=10")
    HTTP_CODE=$(echo "$RESERVATIONS_RESPONSE" | tail -2 | head -1)
    RESPONSE_TIME=$(echo "$RESERVATIONS_RESPONSE" | tail -1)
    RESERVATIONS_BODY=$(echo "$RESERVATIONS_RESPONSE" | head -1)

    if [ "$HTTP_CODE" = "200" ]; then
        print_pass "Reservations retrieved successfully (${RESPONSE_TIME}s)"
        echo "$RESERVATIONS_BODY" | jq '.' > "$TEST_RESULTS_DIR/reservations_response.json"

        # Count reservations
        RESERVATION_COUNT=$(echo "$RESERVATIONS_BODY" | jq '.reservations | length')
        print_info "Total reservations returned: $RESERVATION_COUNT"

        if [ "$RESERVATION_COUNT" -gt 0 ]; then
            print_pass "Reservations found in response"

            # Extract first booking ID for detail test
            FIRST_BOOKING_ID=$(echo "$RESERVATIONS_BODY" | jq -r '.reservations[0].id')
            echo "$FIRST_BOOKING_ID" > "$TEST_RESULTS_DIR/test_booking_id.txt"
            print_info "Test booking ID: $FIRST_BOOKING_ID"
        else
            print_warning "No reservations found in account"
        fi
    else
        print_fail "Reservations retrieval failed with HTTP $HTTP_CODE"
        echo "$RESERVATIONS_BODY"
    fi

    print_test "4.2 - Get Reservation Details"
    if [ -f "$TEST_RESULTS_DIR/test_booking_id.txt" ]; then
        BOOKING_ID=$(cat "$TEST_RESULTS_DIR/test_booking_id.txt")

        BOOKING_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$BASE_URL/api/reservations/$BOOKING_ID")
        HTTP_CODE=$(echo "$BOOKING_RESPONSE" | tail -2 | head -1)
        RESPONSE_TIME=$(echo "$BOOKING_RESPONSE" | tail -1)
        BOOKING_BODY=$(echo "$BOOKING_RESPONSE" | head -1)

        if [ "$HTTP_CODE" = "200" ]; then
            print_pass "Booking details retrieved successfully (${RESPONSE_TIME}s)"
            echo "$BOOKING_BODY" | jq '.' > "$TEST_RESULTS_DIR/booking_details_response.json"

            # Verify booking ID matches
            RETURNED_ID=$(echo "$BOOKING_BODY" | jq -r '.id')
            if [ "$RETURNED_ID" = "$BOOKING_ID" ]; then
                print_pass "Booking ID matches requested ID"
            else
                print_fail "Booking ID mismatch: expected $BOOKING_ID, got $RETURNED_ID"
            fi
        else
            print_fail "Booking details retrieval failed with HTTP $HTTP_CODE"
            echo "$BOOKING_BODY"
        fi
    else
        print_warning "Skipping booking details test (no booking ID available)"
    fi

else
    print_warning "Skipping bookings tests (no access token available)"
fi

# ============================================================================
# PHASE 5: Financial Reporting Operations
# ============================================================================
print_header "PHASE 5: Financial Reporting Operations"

if [ -f "$TEST_RESULTS_DIR/access_token.txt" ]; then
    ACCESS_TOKEN=$(cat "$TEST_RESULTS_DIR/access_token.txt")

    print_test "5.1 - Get Financial Analytics"
    START_DATE=$(date -u -v-30d +"%Y-%m-%d" 2>/dev/null || date -u -d "-30 days" +"%Y-%m-%d")
    END_DATE=$(date -u +"%Y-%m-%d")

    FINANCIAL_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/analytics/financial?start_date=$START_DATE&end_date=$END_DATE")
    HTTP_CODE=$(echo "$FINANCIAL_RESPONSE" | tail -2 | head -1)
    RESPONSE_TIME=$(echo "$FINANCIAL_RESPONSE" | tail -1)
    FINANCIAL_BODY=$(echo "$FINANCIAL_RESPONSE" | head -1)

    if [ "$HTTP_CODE" = "200" ]; then
        print_pass "Financial analytics retrieved successfully (${RESPONSE_TIME}s)"
        echo "$FINANCIAL_BODY" | jq '.' > "$TEST_RESULTS_DIR/financial_analytics_response.json"

        # Extract key metrics
        TOTAL_REVENUE=$(echo "$FINANCIAL_BODY" | jq -r '.total_revenue')
        AVG_RATE=$(echo "$FINANCIAL_BODY" | jq -r '.average_rate')
        print_info "Total revenue: $TOTAL_REVENUE"
        print_info "Average rate: $AVG_RATE"
    else
        print_fail "Financial analytics retrieval failed with HTTP $HTTP_CODE"
        echo "$FINANCIAL_BODY"
    fi

else
    print_warning "Skipping financial tests (no access token available)"
fi

# ============================================================================
# PHASE 6: Response Validation & Headers
# ============================================================================
print_header "PHASE 6: Response Validation & Headers"

print_test "6.1 - Check Rate Limiting Headers"
HEADERS_RESPONSE=$(curl -s -i "$BASE_URL/health" 2>&1 | grep -i "x-ratelimit")
if [ ! -z "$HEADERS_RESPONSE" ]; then
    print_pass "Rate limiting headers present"
    echo "$HEADERS_RESPONSE"
else
    print_warning "Rate limiting headers not found"
fi

print_test "6.2 - Check CORS Headers"
CORS_RESPONSE=$(curl -s -i -H "Origin: http://example.com" "$BASE_URL/health" 2>&1 | grep -i "access-control")
if [ ! -z "$CORS_RESPONSE" ]; then
    print_pass "CORS headers present"
    echo "$CORS_RESPONSE"
else
    print_warning "CORS headers not found"
fi

print_test "6.3 - Check Response Content-Type"
CONTENT_TYPE=$(curl -s -i "$BASE_URL/health" 2>&1 | grep -i "content-type")
if echo "$CONTENT_TYPE" | grep -q "application/json"; then
    print_pass "Content-Type is application/json"
else
    print_warning "Content-Type might not be correct: $CONTENT_TYPE"
fi

# ============================================================================
# PHASE 7: Error Handling
# ============================================================================
print_header "PHASE 7: Error Handling"

print_test "7.1 - Test 404 Not Found"
NOT_FOUND_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/nonexistent/endpoint")
HTTP_CODE=$(echo "$NOT_FOUND_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "404" ]; then
    print_pass "404 Not Found handled correctly"
else
    print_fail "404 Not Found not handled correctly (got $HTTP_CODE)"
fi

print_test "7.2 - Test Invalid JSON"
INVALID_JSON_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{invalid json}" \
    "$BASE_URL/auth/authenticate")
HTTP_CODE=$(echo "$INVALID_JSON_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    print_pass "Invalid JSON handled correctly (HTTP $HTTP_CODE)"
else
    print_warning "Invalid JSON handling returned unexpected code: $HTTP_CODE"
fi

print_test "7.3 - Test Missing Required Fields"
MISSING_FIELDS_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{}" \
    "$BASE_URL/auth/authenticate")
HTTP_CODE=$(echo "$MISSING_FIELDS_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "422" ]; then
    print_pass "Missing required fields handled correctly"
else
    print_warning "Missing fields handling returned unexpected code: $HTTP_CODE"
fi

print_test "7.4 - Test Unauthorized Access"
UNAUTHORIZED_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/listings")
HTTP_CODE=$(echo "$UNAUTHORIZED_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    print_pass "Unauthorized access handled correctly (HTTP $HTTP_CODE)"
else
    print_warning "Unauthorized access returned unexpected code: $HTTP_CODE"
fi

# ============================================================================
# PHASE 8: Performance Metrics
# ============================================================================
print_header "PHASE 8: Performance Metrics"

print_test "8.1 - Measure Health Endpoint Performance"
PERF_TIMES=()
for i in {1..10}; do
    TIME=$(curl -s -w "%{time_total}" -o /dev/null "$BASE_URL/health")
    PERF_TIMES+=($TIME)
done

# Calculate average
AVG_TIME=$(echo "${PERF_TIMES[@]}" | awk '{sum=0; for(i=1; i<=NF; i++) sum+=$i; print sum/NF}')
print_info "Average response time (10 requests): ${AVG_TIME}s"

if (( $(echo "$AVG_TIME < 0.5" | bc -l) )); then
    print_pass "Average response time is excellent (<0.5s)"
elif (( $(echo "$AVG_TIME < 1.0" | bc -l) )); then
    print_pass "Average response time is good (<1.0s)"
else
    print_warning "Average response time is slow (${AVG_TIME}s)"
fi

# ============================================================================
# Final Summary
# ============================================================================
print_header "TEST SUMMARY"

echo -e "Total Tests:     $TOTAL_TESTS"
echo -e "${GREEN}Passed:          $PASSED_TESTS${NC}"
echo -e "${RED}Failed:          $FAILED_TESTS${NC}"
echo -e "${YELLOW}Warnings:        $WARNINGS${NC}"

PASS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
echo -e "\nPass Rate:       ${PASS_RATE}%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL TESTS PASSED${NC}"
    EXIT_CODE=0
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}"
    EXIT_CODE=1
fi

print_info "Detailed results saved to: $TEST_RESULTS_DIR"

# Generate JSON summary
cat > "$TEST_RESULTS_DIR/test_summary.json" <<EOF
{
  "test_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "server_url": "$BASE_URL",
  "total_tests": $TOTAL_TESTS,
  "passed": $PASSED_TESTS,
  "failed": $FAILED_TESTS,
  "warnings": $WARNINGS,
  "pass_rate": $PASS_RATE,
  "exit_code": $EXIT_CODE
}
EOF

print_info "JSON summary saved to: $TEST_RESULTS_DIR/test_summary.json"

exit $EXIT_CODE
