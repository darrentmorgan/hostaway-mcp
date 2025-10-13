# Data Model: Guest Communication & Enhanced Error Handling (v1.1)

**Date**: 2025-10-13
**Branch**: `002-enhance-the-hostaway`
**Input**: Research findings from `research.md`, functional requirements FR-001 to FR-018

---

## Overview

v1.1 introduces 6 new entities to support guest communication, partial failure handling, and message search. All models use Pydantic for type safety and validation, following v1.0 patterns.

### New Entities

1. **Message** - Individual communication between guest and property manager
2. **ConversationThread** - Collection of messages for a booking
3. **PartialFailureResponse[T]** - Generic batch operation response
4. **BatchFailure** - Individual failed item in batch operation
5. **BatchSummary** - Metrics for batch operation
6. **MessageSearchCriteria** - Filter parameters for message queries

---

## Entity Definitions

### 1. Message

**Purpose**: Represents a single message in a guest conversation

**Source**: Hostaway Conversations API (`GET /v1/conversations/{id}/messages`)

**Requirements**: FR-001 to FR-006, FR-016, FR-018

```python
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class MessageChannel(str, Enum):
    """Communication channel types"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PLATFORM = "platform"  # Airbnb, Booking.com, VRBO, etc.

class SenderType(str, Enum):
    """Message sender classification"""
    GUEST = "guest"
    SYSTEM = "system"
    PROPERTY_MANAGER = "property_manager"

class DeliveryStatus(str, Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class Message(BaseModel):
    """Individual message in a conversation"""

    id: str = Field(..., description="Unique message identifier from Hostaway")
    booking_id: int = Field(..., gt=0, description="Associated booking/reservation ID")
    content: str = Field(..., min_length=1, description="Message text content")
    timestamp: datetime = Field(..., description="When message was sent (UTC)")
    channel: MessageChannel = Field(..., description="Communication channel")
    sender_type: SenderType = Field(..., description="Who sent the message")
    sender_id: str = Field(..., description="Sender identifier (guest_id, pm_id, system)")
    recipient_id: str = Field(..., description="Recipient identifier")
    delivery_status: DeliveryStatus = Field(
        default=DeliveryStatus.SENT,
        description="Current delivery status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_abc123",
                "booking_id": 12345,
                "content": "What time is check-in?",
                "timestamp": "2025-10-13T14:30:00Z",
                "channel": "platform",
                "sender_type": "guest",
                "sender_id": "guest_xyz",
                "recipient_id": "pm_789",
                "delivery_status": "delivered"
            }
        }
```

**Validation Rules**:
- `content`: Must be non-empty string (min_length=1)
- `booking_id`: Must be positive integer (gt=0)
- `timestamp`: Required, must be valid datetime (UTC assumed)
- `channel`: Must be one of enum values (email, sms, in_app, platform)
- `sender_type`: Must be one of enum values (guest, system, property_manager)

**Mapping from Hostaway API**:
```python
# Hostaway response → Message model
{
    "id": "msg_123",                    → id
    "reservationId": 12345,             → booking_id
    "content": "Message text",          → content
    "createdAt": "2025-10-13T...",      → timestamp
    "channelType": "airbnb",            → channel (map to MessageChannel.PLATFORM)
    "direction": "in",                  → sender_type (in=GUEST, out=PROPERTY_MANAGER/SYSTEM)
    "sender": {"id": "..."},            → sender_id
    "recipient": {"id": "..."}          → recipient_id
}
```

---

### 2. ConversationThread

**Purpose**: Aggregates all messages for a booking into chronological timeline

**Requirements**: FR-004, FR-006

```python
from typing import List, Set
from pydantic import BaseModel, Field, field_validator

class ConversationThread(BaseModel):
    """Complete conversation history for a booking"""

    booking_id: int = Field(..., gt=0, description="Booking identifier")
    messages: List[Message] = Field(
        default_factory=list,
        description="Messages ordered chronologically (oldest first)"
    )
    total_count: int = Field(..., ge=0, description="Total messages in thread")
    channels_used: Set[MessageChannel] = Field(
        default_factory=set,
        description="Unique channels present in conversation"
    )

    @field_validator("messages")
    @classmethod
    def messages_ordered_chronologically(cls, messages: List[Message]) -> List[Message]:
        """Ensure messages are sorted by timestamp"""
        return sorted(messages, key=lambda m: m.timestamp)

    @field_validator("total_count")
    @classmethod
    def total_matches_messages(cls, total_count: int, info) -> int:
        """Validate total_count matches messages list length"""
        messages = info.data.get("messages", [])
        if len(messages) != total_count:
            raise ValueError(f"total_count ({total_count}) must match messages length ({len(messages)})")
        return total_count

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": 12345,
                "messages": [
                    {"id": "msg_1", "timestamp": "2025-10-10T10:00:00Z", "...": "..."},
                    {"id": "msg_2", "timestamp": "2025-10-11T15:30:00Z", "...": "..."}
                ],
                "total_count": 2,
                "channels_used": ["email", "platform"]
            }
        }
```

**Validation Rules**:
- `booking_id`: Must be positive integer
- `messages`: Automatically sorted by timestamp (validator enforces)
- `total_count`: Must equal `len(messages)` (validator enforces)
- `channels_used`: Derived from message list (set of unique channels)

**Construction Logic**:
```python
# Pseudocode for building ConversationThread
def build_conversation(booking_id: int, messages: List[Message]) -> ConversationThread:
    channels = {m.channel for m in messages}
    return ConversationThread(
        booking_id=booking_id,
        messages=messages,  # Will be auto-sorted by validator
        total_count=len(messages),
        channels_used=channels
    )
```

---

### 3. PartialFailureResponse[T]

**Purpose**: Generic response for batch operations supporting partial failures

**Requirements**: FR-007 to FR-011

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')

class PartialFailureResponse(BaseModel, Generic[T]):
    """Response for batch operations with partial success/failure support"""

    successful_results: List[T] = Field(
        default_factory=list,
        description="Successfully processed items"
    )
    failed_items: List["BatchFailure"] = Field(
        default_factory=list,
        description="Failed items with error details"
    )
    summary: "BatchSummary" = Field(..., description="Batch operation metrics")

    @field_validator("summary")
    @classmethod
    def validate_summary_totals(cls, summary: "BatchSummary", info) -> "BatchSummary":
        """Ensure summary totals match actual results"""
        successful = len(info.data.get("successful_results", []))
        failed = len(info.data.get("failed_items", []))

        if summary.succeeded != successful:
            raise ValueError(f"summary.succeeded ({summary.succeeded}) must match successful_results length ({successful})")
        if summary.failed != failed:
            raise ValueError(f"summary.failed ({summary.failed}) must match failed_items length ({failed})")
        if summary.total_attempted != successful + failed:
            raise ValueError(f"summary.total_attempted must equal succeeded + failed")

        return summary

    class Config:
        json_schema_extra = {
            "example": {
                "successful_results": [
                    {"id": 101, "name": "Property A"},
                    {"id": 102, "name": "Property B"}
                ],
                "failed_items": [
                    {
                        "item_id": "999",
                        "error_type": "not_found",
                        "error_message": "Property 999 not found",
                        "remediation": "Verify property ID exists in Hostaway"
                    }
                ],
                "summary": {
                    "total_attempted": 3,
                    "succeeded": 2,
                    "failed": 1,
                    "success_rate": 0.6667
                }
            }
        }
```

**Usage Examples**:
```python
# Batch property retrieval
PartialFailureResponse[List[Property]]

# Batch booking retrieval
PartialFailureResponse[List[Booking]]

# Batch message search
PartialFailureResponse[List[Message]]
```

---

### 4. BatchFailure

**Purpose**: Represents a single failed item in a batch operation

**Requirements**: FR-008, FR-011

```python
class ErrorType(str, Enum):
    """Categorized error types for batch failures"""
    NOT_FOUND = "not_found"           # 404: Resource doesn't exist
    UNAUTHORIZED = "unauthorized"      # 403: Permission denied
    VALIDATION_ERROR = "validation_error"  # 422: Invalid input
    RATE_LIMIT = "rate_limit"         # 429: Too many requests
    TIMEOUT = "timeout"               # 504: Upstream timeout
    INTERNAL_ERROR = "internal_error" # 500: Unexpected failure

class BatchFailure(BaseModel):
    """Individual failed item in batch operation"""

    item_id: str = Field(..., description="Identifier of failed item")
    error_type: ErrorType = Field(..., description="Categorized error type")
    error_message: str = Field(..., min_length=1, description="Human-readable error description")
    remediation: str = Field(..., min_length=1, description="Actionable guidance for resolution")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "property_999",
                "error_type": "not_found",
                "error_message": "Property with ID 999 does not exist in Hostaway",
                "remediation": "Verify the property ID exists. Use GET /api/listings to see available properties."
            }
        }
```

**Remediation Templates**:
```python
REMEDIATION_TEMPLATES = {
    ErrorType.NOT_FOUND: "Verify {item_type} ID '{item_id}' exists in Hostaway. Use GET /api/{endpoint} to see available items.",
    ErrorType.UNAUTHORIZED: "Check API permissions for accessing {item_type} '{item_id}'. Verify API key has required scopes.",
    ErrorType.VALIDATION_ERROR: "Fix validation error for {item_type} '{item_id}': {validation_detail}",
    ErrorType.RATE_LIMIT: "Retry after {retry_after} seconds or reduce request rate. Current limit: {limit} req/{period}.",
    ErrorType.TIMEOUT: "Upstream service timeout for {item_type} '{item_id}'. Retry with exponential backoff.",
    ErrorType.INTERNAL_ERROR: "Unexpected error processing {item_type} '{item_id}'. Contact support if issue persists."
}
```

---

### 5. BatchSummary

**Purpose**: Provides metrics for batch operation results

**Requirements**: FR-010

```python
from pydantic import BaseModel, Field, field_validator

class BatchSummary(BaseModel):
    """Summary metrics for batch operation"""

    total_attempted: int = Field(..., ge=0, description="Total items in batch")
    succeeded: int = Field(..., ge=0, description="Successfully processed items")
    failed: int = Field(..., ge=0, description="Failed items")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Succeeded / Total (0.0 to 1.0)")

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, success_rate: float, info) -> float:
        """Ensure success_rate matches succeeded/total calculation"""
        total = info.data.get("total_attempted", 0)
        succeeded = info.data.get("succeeded", 0)

        if total == 0:
            expected_rate = 0.0
        else:
            expected_rate = succeeded / total

        if abs(success_rate - expected_rate) > 0.001:  # Float precision tolerance
            raise ValueError(f"success_rate ({success_rate}) must equal succeeded/total ({expected_rate})")

        return success_rate

    @field_validator("total_attempted")
    @classmethod
    def total_equals_sum(cls, total: int, info) -> int:
        """Validate total = succeeded + failed"""
        succeeded = info.data.get("succeeded", 0)
        failed = info.data.get("failed", 0)

        if total != succeeded + failed:
            raise ValueError(f"total_attempted ({total}) must equal succeeded ({succeeded}) + failed ({failed})")

        return total

    class Config:
        json_schema_extra = {
            "example": {
                "total_attempted": 10,
                "succeeded": 8,
                "failed": 2,
                "success_rate": 0.8
            }
        }
```

---

### 6. MessageSearchCriteria

**Purpose**: Filter parameters for message search queries

**Requirements**: FR-001 to FR-003, FR-017

```python
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator

class MessageSearchCriteria(BaseModel):
    """Filter and pagination parameters for message search"""

    booking_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filter messages by booking ID"
    )
    guest_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Partial match search on guest name"
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Filter messages from this date (inclusive)"
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Filter messages until this date (inclusive)"
    )
    channels: Optional[List[MessageChannel]] = Field(
        default=None,
        description="Filter by specific channels (empty = all channels)"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Page size (1-1000, default 50)"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset (default 0)"
    )

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, end_date: Optional[date], info) -> Optional[date]:
        """Validate end_date >= start_date"""
        start_date = info.data.get("start_date")

        if start_date and end_date and end_date < start_date:
            raise ValueError(f"end_date ({end_date}) must be >= start_date ({start_date})")

        return end_date

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": 12345,
                "start_date": "2025-10-01",
                "end_date": "2025-10-15",
                "channels": ["email", "platform"],
                "limit": 50,
                "offset": 0
            }
        }
```

**Validation Rules**:
- `booking_id`: If provided, must be positive integer
- `guest_name`: If provided, 1-255 characters (prevent excessive length)
- `start_date` / `end_date`: end_date must be >= start_date
- `channels`: If provided, must be list of valid MessageChannel enum values
- `limit`: 1-1000 (enforced by Field constraint)
- `offset`: Non-negative integer

---

## Relationships

```
ConversationThread 1 ─┬─ * Message
                      │   (booking_id foreign key)
                      │
                      └─> booking_id references Booking.id (from v1.0)

PartialFailureResponse[T] 1 ─┬─ * T (successful_results)
                              ├─ * BatchFailure (failed_items)
                              └─ 1 BatchSummary

MessageSearchCriteria ──> used by GET /api/messages endpoint
```

---

## File Organization

### New Model Files

```
src/models/
├── messages.py           # Message, ConversationThread, MessageChannel, SenderType, DeliveryStatus
├── batch.py              # PartialFailureResponse, BatchFailure, BatchSummary, ErrorType
└── search.py             # MessageSearchCriteria
```

### Import Structure

```python
# In src/models/messages.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import List, Set

# In src/models/batch.py
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Generic, TypeVar, List

# In src/models/search.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
from src.models.messages import MessageChannel
```

---

## Data Model Complete

All entities defined with:
- ✅ Pydantic models with type safety
- ✅ Field validation (constraints, enums)
- ✅ Custom validators for business logic
- ✅ Example schemas for documentation
- ✅ Relationship mapping

**Next**: Generate API contracts (OpenAPI schemas)
