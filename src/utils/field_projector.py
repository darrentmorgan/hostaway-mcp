"""Field projection utility for response summarization.

Extracts essential fields from objects to reduce token usage.
Based on research.md R003: Field projection (primary) + extractive (secondary).
"""

from typing import Any


def project_fields(obj: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Project specified fields from an object.

    Args:
        obj: Source object (dictionary)
        fields: List of field names to extract (supports nested paths with dot notation)

    Returns:
        New dict containing only the specified fields

    Example:
        >>> booking = {
        ...     "id": "BK12345",
        ...     "status": "confirmed",
        ...     "guestName": "John Doe",
        ...     "guestEmail": "john@example.com",
        ...     "guestAddress": {"city": "NYC", "state": "NY"},
        ...     "priceBreakdown": {...}  # 15 fields
        ... }
        >>> project_fields(booking, ["id", "status", "guestName", "guestAddress.city"])
        {'id': 'BK12345', 'status': 'confirmed', 'guestName': 'John Doe',
         'guestAddress': {'city': 'NYC'}}
    """
    result: dict[str, Any] = {}

    for field in fields:
        # Handle nested field paths (e.g., "guestAddress.city")
        if "." in field:
            parts = field.split(".")
            value = obj
            for part in parts[:-1]:
                value = value.get(part, {})
                if not isinstance(value, dict):
                    break
            else:
                # Successfully traversed to parent
                final_key = parts[-1]
                if isinstance(value, dict) and final_key in value:
                    # Build nested structure in result
                    current = result
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[final_key] = value[final_key]
        else:
            # Simple field
            if field in obj:
                result[field] = obj[field]

    return result


def get_essential_fields(obj_type: str) -> list[str]:
    """Get essential field list for common object types.

    Args:
        obj_type: Type identifier (e.g., "booking", "listing", "financial_transaction")

    Returns:
        List of essential field names for summarization

    Example:
        >>> get_essential_fields("booking")
        ['id', 'status', 'guestName', 'checkInDate', 'checkOutDate', 'totalPrice', 'propertyId']
    """
    # Essential fields per object type (based on data-model.md examples)
    field_map: dict[str, list[str]] = {
        "booking": [
            "id",
            "status",
            "guestName",
            "checkInDate",
            "checkOutDate",
            "totalPrice",
            "currency",
            "propertyId",
        ],
        "listing": [
            "id",
            "name",
            "status",
            "address",
            "maxGuests",
            "bedroomCount",
            "bathroomCount",
            "basePrice",
        ],
        "financial_transaction": [
            "id",
            "type",
            "amount",
            "currency",
            "status",
            "bookingId",
            "createdAt",
        ],
        "conversation": [
            "id",
            "bookingId",
            "guestName",
            "lastMessageAt",
            "unreadCount",
            "status",
        ],
        "review": [
            "id",
            "bookingId",
            "rating",
            "comment",
            "createdAt",
            "guestName",
        ],
    }

    return field_map.get(obj_type, ["id"])  # Fallback to just ID


def estimate_field_count(obj: dict[str, Any]) -> int:
    """Recursively count total fields in an object.

    Args:
        obj: Object to analyze

    Returns:
        Total number of fields (including nested)

    Example:
        >>> booking = {"id": "BK12345", "guestAddress": {"city": "NYC", "state": "NY"}}
        >>> estimate_field_count(booking)
        4  # id, guestAddress, guestAddress.city, guestAddress.state
    """
    count = 0
    for value in obj.values():
        count += 1
        if isinstance(value, dict):
            count += estimate_field_count(value)
        elif isinstance(value, list):
            # For lists, count fields in first item (assume homogeneous)
            if value and isinstance(value[0], dict):
                count += estimate_field_count(value[0])
    return count


def calculate_projection_ratio(
    original: dict[str, Any],
    projected: dict[str, Any],
) -> float:
    """Calculate field reduction ratio after projection.

    Args:
        original: Original object
        projected: Projected object

    Returns:
        Ratio of fields retained (0.0 to 1.0)

    Example:
        >>> original = {"id": "BK12345", "field1": 1, "field2": 2, "field3": 3}
        >>> projected = {"id": "BK12345", "field1": 1}
        >>> calculate_projection_ratio(original, projected)
        0.5  # 2 out of 4 fields retained
    """
    original_count = estimate_field_count(original)
    projected_count = estimate_field_count(projected)

    if original_count == 0:
        return 1.0

    return projected_count / original_count
