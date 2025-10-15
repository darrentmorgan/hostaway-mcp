# OpenAPI Documentation: Cursor-Based Pagination

**Version**: 1.0
**Date**: October 15, 2025
**API Version**: v1

## Accessing API Documentation

The Hostaway MCP Server provides auto-generated OpenAPI documentation via FastAPI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Pagination Schema Definitions

### PaginatedResponse[T]

Generic paginated response wrapper for all list endpoints.

```yaml
PaginatedResponse:
  type: object
  required:
    - items
    - nextCursor
    - meta
  properties:
    items:
      type: array
      description: Array of items for the current page
      items:
        $ref: '#/components/schemas/T'
    nextCursor:
      type: string
      nullable: true
      description: |
        Opaque cursor token for fetching the next page.
        null if this is the last page.
      example: "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ=="
    meta:
      $ref: '#/components/schemas/PageMetadata'
```

### PageMetadata

Metadata about the current page and pagination state.

```yaml
PageMetadata:
  type: object
  required:
    - totalCount
    - pageSize
    - hasMore
  properties:
    totalCount:
      type: integer
      description: Estimated total number of items available
      example: 150
    pageSize:
      type: integer
      description: Number of items in the current page
      example: 50
    hasMore:
      type: boolean
      description: Whether more pages are available
      example: true
```

## Updated Endpoint Specifications

### GET /api/listings

Retrieve property listings with cursor-based pagination.

#### Request

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 50 | Maximum items per page (1-200) |
| `cursor` | string | No | null | Pagination cursor from previous response |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-API-Key` | string | Yes | API authentication key |

#### Response

**Status: 200 OK**

```json
{
  "items": [
    {
      "id": 12345,
      "name": "Luxury Beachfront Condo",
      "address": "123 Ocean Drive",
      "city": "Miami",
      "bedrooms": 2,
      "bathrooms": 2.0,
      "maxGuests": 4
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 150,
    "pageSize": 50,
    "hasMore": true
  }
}
```

**Status: 400 Bad Request** - Invalid cursor

```json
{
  "detail": "Invalid cursor: Signature verification failed"
}
```

**Status: 401 Unauthorized** - Missing or invalid API key

```json
{
  "detail": "Missing API key. Provide X-API-Key header."
}
```

#### OpenAPI 3.0 Schema

```yaml
paths:
  /api/listings:
    get:
      summary: Get all property listings
      description: |
        Retrieve all property listings with cursor-based pagination support.

        ## Pagination

        This endpoint uses cursor-based pagination for efficient navigation
        through large result sets. Use the `nextCursor` from the response
        to fetch subsequent pages.

        ## Example Usage

        First page:
        ```
        GET /api/listings?limit=50
        ```

        Next page:
        ```
        GET /api/listings?cursor=eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==
        ```

      tags:
        - Listings
      operationId: get_listings
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 200
            default: 50
          description: Maximum results per page
        - name: cursor
          in: query
          required: false
          schema:
            type: string
            nullable: true
          description: Pagination cursor from previous response
      security:
        - ApiKeyAuth: []
      responses:
        '200':
          description: Successful response with paginated listings
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedResponse_Listing'
              examples:
                first_page:
                  summary: First page of results
                  value:
                    items:
                      - id: 12345
                        name: "Luxury Beachfront Condo"
                    nextCursor: "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ=="
                    meta:
                      totalCount: 150
                      pageSize: 50
                      hasMore: true
                last_page:
                  summary: Last page of results
                  value:
                    items:
                      - id: 12399
                        name: "Mountain Cabin"
                    nextCursor: null
                    meta:
                      totalCount: 150
                      pageSize: 25
                      hasMore: false
        '400':
          description: Bad request - invalid cursor
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
              example:
                detail: "Invalid cursor: Signature verification failed"
        '401':
          description: Unauthorized - missing or invalid API key
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
              example:
                detail: "Missing API key. Provide X-API-Key header."
```

### GET /api/reservations

Search and filter bookings/reservations with cursor-based pagination.

#### Request

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Maximum items per page (1-200) |
| `cursor` | string | No | null | Pagination cursor from previous response |
| `listing_id` | integer | No | null | Filter by property ID |
| `status` | string | No | null | Comma-separated booking statuses |
| `check_in_from` | string | No | null | Check-in date range start (YYYY-MM-DD) |
| `check_in_to` | string | No | null | Check-in date range end (YYYY-MM-DD) |
| `check_out_from` | string | No | null | Check-out date range start (YYYY-MM-DD) |
| `check_out_to` | string | No | null | Check-out date range end (YYYY-MM-DD) |
| `guest_email` | string | No | null | Filter by guest email |
| `booking_source` | string | No | null | Filter by booking source |
| `min_guests` | integer | No | null | Minimum number of guests |
| `max_guests` | integer | No | null | Maximum number of guests |

#### Response

**Status: 200 OK**

```json
{
  "items": [
    {
      "id": 987654,
      "listingId": 12345,
      "guestName": "John Doe",
      "checkIn": "2025-11-01",
      "checkOut": "2025-11-07",
      "status": "confirmed",
      "totalPrice": 1500.00
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjEwMCwidHMiOjE2OTc0NTI4MDAuMH0=",
  "meta": {
    "totalCount": 523,
    "pageSize": 100,
    "hasMore": true
  }
}
```

#### OpenAPI 3.0 Schema

```yaml
paths:
  /api/reservations:
    get:
      summary: Search bookings/reservations
      description: |
        Search and filter bookings/reservations with cursor-based pagination.

        Supports multiple filter criteria that can be combined.
        All filters are applied using AND logic.

      tags:
        - Bookings
      operationId: search_bookings
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 200
            default: 100
        - name: cursor
          in: query
          schema:
            type: string
            nullable: true
        - name: listing_id
          in: query
          schema:
            type: integer
            nullable: true
        - name: status
          in: query
          schema:
            type: string
            nullable: true
          description: Comma-separated list (e.g., "confirmed,pending")
      security:
        - ApiKeyAuth: []
      responses:
        '200':
          description: Successful response with paginated bookings
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedResponse_Booking'
```

## Security Schemes

```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: |
        API key authentication for MCP endpoints.

        Obtain an API key from the dashboard at /dashboard/api-keys.

        Example:
        ```
        X-API-Key: mcp_abcd1234efgh5678ijkl9012mnop3456
        ```
```

## Component Schemas

### Complete Schema Definitions

```yaml
components:
  schemas:
    PaginatedResponse_Listing:
      type: object
      required: [items, nextCursor, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Listing'
        nextCursor:
          type: string
          nullable: true
        meta:
          $ref: '#/components/schemas/PageMetadata'

    PaginatedResponse_Booking:
      type: object
      required: [items, nextCursor, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Booking'
        nextCursor:
          type: string
          nullable: true
        meta:
          $ref: '#/components/schemas/PageMetadata'

    PageMetadata:
      type: object
      required: [totalCount, pageSize, hasMore]
      properties:
        totalCount:
          type: integer
          description: Estimated total count
        pageSize:
          type: integer
          description: Items in current page
        hasMore:
          type: boolean
          description: More pages available

    Listing:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        address:
          type: string
        city:
          type: string
        bedrooms:
          type: integer
        bathrooms:
          type: number
        maxGuests:
          type: integer

    Booking:
      type: object
      properties:
        id:
          type: integer
        listingId:
          type: integer
        guestName:
          type: string
        checkIn:
          type: string
          format: date
        checkOut:
          type: string
          format: date
        status:
          type: string
        totalPrice:
          type: number

    HTTPValidationError:
      type: object
      properties:
        detail:
          type: string
```

## Code Generation

### TypeScript Client

Generate TypeScript client from OpenAPI spec:

```bash
# Install openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Generate client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./src/generated/api-client
```

### Python Client

```bash
# Install openapi-generator
pip install openapi-python-client

# Generate client
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output-path ./generated
```

## Testing with OpenAPI

### Swagger UI Testing

1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" and enter your API key
3. Expand `/api/listings` endpoint
4. Click "Try it out"
5. Set `limit=10`
6. Click "Execute"
7. Copy `nextCursor` from response
8. Execute again with the cursor

### cURL Examples

```bash
# First page
curl -X GET "http://localhost:8000/api/listings?limit=50" \
  -H "X-API-Key: mcp_your_key_here"

# Next page (use cursor from previous response)
curl -X GET "http://localhost:8000/api/listings?cursor=eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==" \
  -H "X-API-Key: mcp_your_key_here"

# With filters
curl -X GET "http://localhost:8000/api/reservations?limit=100&status=confirmed&listing_id=123" \
  -H "X-API-Key: mcp_your_key_here"
```

## Postman Collection

### Import OpenAPI Spec

1. Open Postman
2. Click "Import"
3. Enter URL: `http://localhost:8000/openapi.json`
4. Postman will generate a collection with all endpoints

### Configure Environment

Create a Postman environment with:
- `baseUrl`: `http://localhost:8000`
- `apiKey`: `mcp_your_key_here`

### Test Pagination Flow

Create a test collection:

```javascript
// Test: Get first page
pm.test("First page returns items", function () {
    const response = pm.response.json();
    pm.expect(response.items).to.be.an('array');
    pm.expect(response.items.length).to.be.above(0);

    // Save cursor for next request
    if (response.nextCursor) {
        pm.environment.set("cursor", response.nextCursor);
    }
});

// Test: Get next page using cursor
pm.test("Second page returns different items", function () {
    const cursor = pm.environment.get("cursor");
    pm.expect(cursor).to.not.be.null;

    const response = pm.response.json();
    pm.expect(response.items).to.be.an('array');
});
```

## Deprecation Notice

### Removed Parameters

The following query parameters have been **removed** from pagination endpoints:

- ~~`offset`~~ - Replaced by `cursor`

### Deprecated Response Fields

The following response fields are **deprecated** and will be removed in v2.0:

- ~~`listings`~~ - Use `items` instead
- ~~`bookings`~~ - Use `items` instead
- ~~Top-level `count`~~ - Use `meta.totalCount` instead
- ~~Top-level `limit`~~ - Use `meta.pageSize` instead
- ~~Top-level `offset`~~ - No longer applicable

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 15, 2025 | Initial cursor-based pagination release |

## References

- [Migration Guide](./PAGINATION_MIGRATION.md)
- [Context Protection Docs](./CONTEXT_PROTECTION.md)
- [FastAPI OpenAPI Docs](https://fastapi.tiangolo.com/tutorial/metadata/)

---

**Last Updated**: October 15, 2025
**Maintained By**: API Team
