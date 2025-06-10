# backend/app/src/schemas/base.py

"""
This module defines base Pydantic schemas and common utility schemas
used throughout the application for API request/response models and data validation.
"""

import logging
from datetime import datetime, timezone # Added timezone
from typing import List, Optional, TypeVar, Generic, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_camel

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Generic TypeVar for Paginated Responses & Data Responses ---
DataType = TypeVar('DataType')

# --- Pydantic Model Configuration ---
# Common configuration for Pydantic models
# - from_attributes=True (formerly orm_mode=True): Allows creating schemas from ORM model instances.
# - populate_by_name=True: Allows using field aliases in input data (e.g., if API uses camelCase but model uses snake_case).
# - alias_generator=to_camel: Automatically generates camelCase aliases for fields.
class BaseSchema(BaseModel):
    """
    Base Pydantic schema that all other schemas should inherit from.
    Includes common configuration for ORM mode (from_attributes) and alias generation.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        # extra='ignore', # Or 'forbid' to prevent unexpected fields
        # json_encoders for specific types like datetime if needed, though Pydantic handles datetime well by default.
    )

# --- Mixin Schemas for Common Fields ---

class IDSchemaMixin(BaseModel): # Does not need to inherit BaseSchema if it's just a field provider
    """Mixin for schemas that include an 'id' field."""
    id: int = Field(..., description="Unique identifier for the resource", example=1)

class TimestampSchemaMixin(BaseModel):
    """Mixin for schemas that include 'created_at' and 'updated_at' fields."""
    created_at: datetime = Field(..., description="Timestamp of when the resource was created (UTC)", example=datetime.now(timezone.utc))
    updated_at: datetime = Field(..., description="Timestamp of the last update to the resource (UTC)", example=datetime.now(timezone.utc))

class SoftDeleteSchemaMixin(BaseModel):
    """Mixin for schemas that include an optional 'deleted_at' field for soft-deleted resources."""
    deleted_at: Optional[datetime] = Field(None, description="Timestamp of when the resource was soft-deleted (UTC), if applicable", example=None)

# --- Base Response Schemas ---

class BaseResponseSchema(BaseSchema, IDSchemaMixin, TimestampSchemaMixin):
    """
    A common base for many response schemas, including ID and timestamps.
    Inherits from BaseSchema for common Pydantic config.
    """
    pass # Fields are inherited from mixins

class BaseMainResponseSchema(BaseResponseSchema, SoftDeleteSchemaMixin):
    """
    Base schema for main business entities, mirroring `models.base.BaseMainModel`.
    Includes ID, timestamps, soft-delete field, name, description, state, and notes.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Name of the entity", example="My Awesome Item")
    description: Optional[str] = Field(None, description="Optional detailed description of the entity", example="This is a very detailed description.")
    state: Optional[str] = Field(None, max_length=50, description="Current state or status of the entity", example="active")
    notes: Optional[str] = Field(None, description="Internal notes or general remarks about the entity", example="Some internal notes here.")

class BaseDictionaryResponseSchema(BaseMainResponseSchema):
    """
    Base schema for dictionary/lookup table entities, mirroring `models.dictionaries.BaseDictionaryModel`.
    Includes all fields from BaseMainResponseSchema plus code, is_default, and display_order.
    """
    code: str = Field(..., min_length=1, max_length=100, description="Unique code or short identifier for the dictionary item", example="ACTIVE_STATUS")
    is_default: Optional[bool] = Field(None, description="Indicates if this is a default value for the dictionary type", example=False)
    display_order: Optional[int] = Field(None, description="Order in which this item should be displayed in lists/dropdowns", example=1)

# --- Utility Schemas for API Responses ---

class MessageResponse(BaseSchema):
    """Schema for simple status messages from the API."""
    message: str = Field(..., description="A message detailing the result of the operation", example="Operation completed successfully")
    detail: Optional[Any] = Field(None, description="Optional additional details or structured data related to the message")

class DataResponse(BaseSchema, Generic[DataType]):
    """
    Generic schema for wrapping a single data object in a response.
    Ensures consistent response structure: `{"data": {...}}`.
    """
    data: DataType = Field(..., description="The actual data payload of the response")

class PaginationInfo(BaseSchema):
    """
    Schema for pagination metadata included in paginated responses.
    """
    page: int = Field(..., ge=1, description="Current page number", example=1)
    size: int = Field(..., ge=1, description="Number of items per page", example=20)
    total_items: int = Field(..., ge=0, description="Total number of items available", example=100)
    total_pages: int = Field(0, ge=0, description="Total number of pages available", example=5) # Default to 0, calculated by validator
    has_next: bool = Field(False, description="Indicates if there is a next page", example=True) # Default to False
    has_previous: bool = Field(False, description="Indicates if there is a previous page", example=False) # Default to False

    @model_validator(mode='after')
    def calculate_total_pages_and_next_prev(self) -> 'PaginationInfo':
        if self.total_items == 0:
            self.total_pages = 0
            self.has_next = False
            self.has_previous = False
        else:
            self.total_pages = (self.total_items + self.size - 1) // self.size
            self.has_next = self.page < self.total_pages
            self.has_previous = self.page > 1
        if self.page > self.total_pages and self.total_pages > 0:
            logger.warning(f"Page {self.page} requested but total pages is {self.total_pages}. This might indicate an issue.")
            # Depending on API strategy, could raise error or adjust page. Here, we just log.
            # self.page = self.total_pages # Example: cap page at total_pages
        return self

class PaginatedResponse(BaseSchema, Generic[DataType]):
    """
    Generic schema for paginated API responses.
    Includes a list of items and pagination metadata.
    """
    items: List[DataType] = Field(..., description="List of data items for the current page")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


# --- Common Query Parameters Schema (Example) ---
# Often placed in a specific feature's schemas.py or a general `api/deps.py`
class CommonQueryParams(BaseModel): # Does not need BaseSchema if not from ORM and no alias needed
    """Common query parameters for filtering, sorting, and pagination."""
    q: Optional[str] = Field(None, description="Search query string")
    skip: int = Field(0, ge=0, description="Number of items to skip (for pagination offset)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of items to return (page size)") # Max limit can be adjusted
    sort_by: Optional[str] = Field(None, description="Field name to sort by (e.g., 'created_at', 'name')")
    sort_order: Optional[str] = Field("asc", description="Sort order: 'asc' or 'desc'")

    @field_validator('sort_order', mode='before')
    @classmethod
    def validate_sort_order(cls, value: Optional[str]) -> Optional[str]:
        if value:
            val_lower = value.lower()
            if val_lower not in ["asc", "desc"]:
                raise ValueError("sort_order must be 'asc' or 'desc'")
            return val_lower
        return value

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Base Pydantic Schemas --- Demonstration")

    # BaseSchema example (mainly for config)
    class Sample(BaseSchema):
        my_field: str = Field(alias="myFieldInJson")
    sample_obj = Sample(myFieldInJson="test") # type: ignore[call-arg] # Pydantic allows alias in constructor
    logger.info(f"BaseSchema with alias: {sample_obj.model_dump(by_alias=True)}")
    logger.info(f"BaseSchema without alias: {sample_obj.model_dump()}")

    # BaseResponseSchema example
    class ItemResponse(BaseResponseSchema):
        item_name: str
    item_resp = ItemResponse(id=1, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc), item_name="Test Item")
    logger.info(f"ItemResponse (camelCase alias): {item_resp.model_dump_json(by_alias=True, indent=2)}")

    # BaseMainResponseSchema example
    class ProductResponse(BaseMainResponseSchema):
        product_sku: str
    prod_resp = ProductResponse(
        id=2, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        name="Laptop X1", description="High-performance laptop", state="available",
        product_sku="LX1-001"
    )
    logger.info(f"ProductResponse (camelCase alias): {prod_resp.model_dump_json(by_alias=True, indent=2)}")

    # BaseDictionaryResponseSchema example
    class StatusResponse(BaseDictionaryResponseSchema):
        pass
    status_resp = StatusResponse(
        id=1, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        name="Active", code="ACTIVE", description="Entity is active", display_order=1
    )
    logger.info(f"StatusResponse (camelCase alias): {status_resp.model_dump_json(by_alias=True, indent=2)}")

    # MessageResponse
    msg_resp = MessageResponse(message="Resource created successfully")
    logger.info(f"MessageResponse: {msg_resp.model_dump_json(by_alias=True, indent=2)}")

    # DataResponse
    class UserData(BaseSchema):
        user_id: int = Field(alias="userId") # Example with explicit alias for clarity
        username: str
    user_data_obj = UserData(userId=10, username="johndoe") # type: ignore[call-arg]
    data_resp = DataResponse[UserData](data=user_data_obj)
    logger.info(f"DataResponse[UserData]: {data_resp.model_dump_json(by_alias=True, indent=2)}")

    # PaginatedResponse
    items_data = [UserData(userId=i, username=f"user{i}") for i in range(3)] # type: ignore[call-arg]
    page_info = PaginationInfo(page=1, size=3, total_items=10)
    logger.info(f"Calculated total_pages by PaginationInfo: {page_info.total_pages}, has_next: {page_info.has_next}")
    paginated_resp = PaginatedResponse[UserData](items=items_data, pagination=page_info)
    logger.info(f"PaginatedResponse[UserData]: {paginated_resp.model_dump_json(by_alias=True, indent=2)}")

    # CommonQueryParams example
    query_params = CommonQueryParams(q="test search", limit=10, sort_by="name", sort_order="DESC")
    logger.info(f"CommonQueryParams: {query_params.model_dump_json(indent=2)}")
    try:
        CommonQueryParams(sort_order="invalid")
    except ValueError as e:
        logger.info(f"Caught expected validation error for sort_order: {e}")
