"""Token budget models for context window management.

Defines Pydantic models for tracking and enforcing token limits.
Based on data-model.md entity definitions.
"""

from pydantic import BaseModel, Field, computed_field


class TokenBudget(BaseModel):
    """Per-request token limit tracking and threshold enforcement.

    Tracks estimated token usage against configured thresholds and
    determines when summarization should be triggered.

    Attributes:
        threshold: Configured token limit (default: 4000)
        hard_cap: Absolute maximum token limit (default: 12000)
        estimated_tokens: Estimated tokens in candidate response
    """

    threshold: int = Field(
        default=4000,
        gt=0,
        description="Configured token limit",
    )
    hard_cap: int = Field(
        default=12000,
        gt=0,
        description="Absolute maximum token limit",
    )
    estimated_tokens: int = Field(
        ge=0,
        description="Estimated tokens in response",
    )

    @computed_field
    @property
    def budget_used(self) -> float:
        """Calculate percentage of threshold used (0.0-1.0+).

        Returns value > 1.0 if over threshold.

        Returns:
            Budget usage ratio (estimated_tokens / threshold)
        """
        return self.estimated_tokens / self.threshold

    @computed_field
    @property
    def summary_mode(self) -> bool:
        """Determine if summarization should be triggered.

        Returns:
            True if estimated_tokens exceeds threshold
        """
        return self.estimated_tokens > self.threshold

    @computed_field
    @property
    def exceeds_hard_cap(self) -> bool:
        """Check if response exceeds hard cap.

        Returns:
            True if estimated_tokens exceeds hard_cap
        """
        return self.estimated_tokens > self.hard_cap

    def model_post_init(self, __context) -> None:
        """Validate that hard_cap >= threshold."""
        if self.hard_cap < self.threshold:
            raise ValueError("hard_cap must be >= threshold")


class BudgetMetadata(BaseModel):
    """Metadata about token budget enforcement.

    Captures decision-making details for observability.

    Attributes:
        threshold_used: Configured threshold for this request
        estimated_tokens: Actual estimated token count
        budget_ratio: Ratio of tokens to threshold
        action_taken: Action taken (e.g., "paginated", "summarized", "allowed")
        reason: Human-readable explanation
    """

    threshold_used: int = Field(gt=0, description="Threshold applied")
    estimated_tokens: int = Field(ge=0, description="Estimated tokens")
    budget_ratio: float = Field(ge=0.0, description="Usage ratio")
    action_taken: str = Field(description="Action taken")
    reason: str = Field(description="Explanation")


class TokenEstimationResult(BaseModel):
    """Result of token estimation for a response.

    Attributes:
        text_length: Length of text in characters
        estimated_tokens: Estimated token count
        estimation_method: Method used (e.g., "character-based")
        overhead_tokens: Estimated envelope overhead
    """

    text_length: int = Field(ge=0, description="Text length in chars")
    estimated_tokens: int = Field(ge=0, description="Estimated tokens")
    estimation_method: str = Field(
        default="character-based",
        description="Estimation method",
    )
    overhead_tokens: int = Field(
        default=200,
        ge=0,
        description="Envelope overhead",
    )

    @computed_field
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens including overhead.

        Returns:
            Sum of estimated_tokens and overhead_tokens
        """
        return self.estimated_tokens + self.overhead_tokens


class TokenBudgetConfig(BaseModel):
    """Configuration for token budget enforcement.

    Supports per-endpoint overrides and global defaults.

    Attributes:
        output_token_threshold: Default threshold (default: 4000)
        hard_output_token_cap: Absolute maximum (default: 12000)
        default_page_size: Default pagination page size (default: 50)
        max_page_size: Maximum allowed page size (default: 200)
        enable_summarization: Enable automatic summarization (default: True)
        enable_pagination: Enable automatic pagination (default: True)
    """

    output_token_threshold: int = Field(
        default=4000,
        gt=0,
        description="Default token threshold",
    )
    hard_output_token_cap: int = Field(
        default=12000,
        gt=0,
        description="Absolute maximum tokens",
    )
    default_page_size: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Default page size",
    )
    max_page_size: int = Field(
        default=200,
        ge=1,
        description="Maximum page size",
    )
    enable_summarization: bool = Field(
        default=True,
        description="Enable summarization",
    )
    enable_pagination: bool = Field(
        default=True,
        description="Enable pagination",
    )

    def model_post_init(self, __context) -> None:
        """Validate configuration constraints."""
        if self.hard_output_token_cap < self.output_token_threshold:
            raise ValueError("hard_output_token_cap must be >= output_token_threshold")

        if self.max_page_size < self.default_page_size:
            raise ValueError("max_page_size must be >= default_page_size")


class EndpointBudgetOverride(BaseModel):
    """Per-endpoint token budget override.

    Allows customizing token limits for specific endpoints.

    Attributes:
        endpoint_pattern: Endpoint pattern (e.g., "/api/v1/listings")
        threshold: Custom threshold for this endpoint
        hard_cap: Custom hard cap for this endpoint
        page_size: Custom default page size
        summarization_enabled: Enable/disable summarization
        pagination_enabled: Enable/disable pagination
    """

    endpoint_pattern: str = Field(description="Endpoint pattern")
    threshold: int | None = Field(default=None, gt=0)
    hard_cap: int | None = Field(default=None, gt=0)
    page_size: int | None = Field(default=None, ge=1, le=200)
    summarization_enabled: bool | None = Field(default=None)
    pagination_enabled: bool | None = Field(default=None)
