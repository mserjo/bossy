# backend/app/src/schemas/bonuses/account.py

"""
Pydantic schemas for User Accounts (points/currency balances).
"""

import logging
from typing import Optional, List # List for potential transactions in a detailed response
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema
from decimal import Decimal # For balance field

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
# For nested responses
# from ..auth.user import UserPublicProfileResponse # Or UserBasicInfo
# from ..groups.group import GroupResponse # Or GroupBasicInfo
# from .transaction import AccountTransactionResponse # For list of transactions

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=1)
    name: Optional[str] = Field(None, example="John Doe")

class GroupBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    name: str = Field(..., example="Kudos Team")
# --- End of local Basic Info schemas ---


# --- UserAccount Schemas ---

class UserAccountBase(BaseSchema):
    """Base schema for user account data."""
    # user_id and group_id are typically set by the system or derived from context (e.g., path parameters)
    # and might not be part of a generic create/update payload directly handled by user input for these fields.
    # user_id: int = Field(..., description="ID of the user who owns this account.")
    # group_id: int = Field(..., description="ID of the group this account is associated with.")
    balance: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2, description="Current balance of points/currency.", example=Decimal("125.50"))
    currency_name: str = Field(default="points", max_length=50, description="Name of the currency held in this account.", example="Kudos Points")
    last_transaction_at: Optional[datetime] = Field(None, description="Timestamp of the last transaction on this account (UTC).", example=datetime.now(timezone.utc))

class UserAccountCreate(UserAccountBase):
    """
    Schema for creating a new user account.
    Accounts are often created automatically when a user joins a group or when the system initializes a user.
    This schema might be used by an admin or system process.
    Requires user_id and group_id.
    """
    user_id: int = Field(..., description="ID of the user for whom the account is being created.")
    group_id: int = Field(..., description="ID of the group for which the account is being created.")
    # Balance and currency_name can use defaults from UserAccountBase or be overridden here if needed.
    balance: Optional[Decimal] = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2, description="Initial balance.")
    currency_name: Optional[str] = Field(default="points", max_length=50, description="Currency name.")

class UserAccountUpdate(BaseSchema): # Does not inherit UserAccountBase to make all fields explicitly optional
    """
    Schema for updating a user account (e.g., by an admin for corrections).
    Direct balance updates are generally discouraged; transactions should be used.
    This schema is for limited cases like correcting currency name or admin notes if added.
    """
    currency_name: Optional[str] = Field(None, max_length=50, description="New currency name for the account.")
    # last_transaction_at is updated by transactions, not directly here.
    # balance: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="Corrected balance. Use with extreme caution; prefer transactions.")

class UserAccountResponse(BaseResponseSchema, UserAccountBase):
    """
    Schema for representing a user account in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    """
    # Fields from UserAccountBase are: balance, currency_name, last_transaction_at
    # Fields from BaseResponseSchema: id, created_at, updated_at
    user: UserBasicInfo = Field(..., description="Basic information about the account owner.")
    group: GroupBasicInfo = Field(..., description="Basic information about the group this account is associated with.")
    # For a more detailed response, could include recent transactions:
    # from .transaction import AccountTransactionResponse # Import when available
    # recent_transactions: Optional[List[AccountTransactionResponse]] = Field(None, description="List of recent transactions.")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserAccount Schemas --- Demonstration")

    # UserAccountCreate Example
    account_create_data = {
        "userId": 101, # camelCase for user_id
        "groupId": 1,  # camelCase for group_id
        "balance": Decimal("50.00"),
        "currencyName": "Merit Points"
    }
    try:
        create_schema = UserAccountCreate(**account_create_data) # type: ignore[call-arg]
        logger.info(f"UserAccountCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating UserAccountCreate: {e}")

    # UserAccountUpdate Example
    account_update_data = {"currencyName": "Super Merits"}
    update_schema = UserAccountUpdate(**account_update_data) # type: ignore[call-arg]
    logger.info(f"UserAccountUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # UserAccountResponse Example
    user_info_data = {"id": 101, "name": "Jane Doe"}
    group_info_data = {"id": 1, "name": "Sales Team Q1"}
    response_data = {
        "id": 201, # ID of the UserAccount record
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
        "user": user_info_data,
        "group": group_info_data,
        "balance": Decimal("1250.75"),
        "currencyName": "Sales Bucks",
        "lastTransactionAt": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    }
    try:
        response_schema = UserAccountResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"UserAccountResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.user and response_schema.group:
            logger.info(f"  Account for User: '{response_schema.user.name}' in Group: '{response_schema.group.name}'")
    except Exception as e:
        logger.error(f"Error creating UserAccountResponse: {e}")
