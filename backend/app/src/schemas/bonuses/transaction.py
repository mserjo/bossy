# backend/app/src/schemas/bonuses/transaction.py

"""
Pydantic schemas for Account Transactions.
"""

import logging
from typing import Optional, Dict, Any # For Dict, Any in related_entity_details if used
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema
from decimal import Decimal # For amount and balance fields

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
from backend.app.src.models.bonuses.transaction import TransactionTypeEnum # Import Enum from model

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=10)
    name: Optional[str] = Field(None, example="Admin User")

class UserAccountBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    currency_name: str = Field(..., example="Kudos Points")
    user_id: int = Field(..., example=101) # Added for context
    group_id: int = Field(..., example=1)  # Added for context
# --- End of local Basic Info schemas ---


# --- AccountTransaction Schemas ---

class AccountTransactionBase(BaseSchema):
    """Base schema for account transaction data."""
    # account_id is often a path parameter or derived when creating transactions for an account.
    transaction_type: TransactionTypeEnum = Field(..., description="Type of the transaction.", example=TransactionTypeEnum.CREDIT_MANUAL_BONUS)
    amount: Decimal = Field(..., max_digits=10, decimal_places=2, description="Transaction amount; positive for credit, negative for debit.", example=Decimal("50.00"))
    description: Optional[str] = Field(None, description="Human-readable description or reason for the transaction.", example="Bonus for excellent presentation.")
    related_entity_type: Optional[str] = Field(None, max_length=100, description="Type of entity related to this transaction (e.g., 'task', 'reward').", example="manual_adjustment")
    related_entity_id: Optional[int] = Field(None, description="ID of the related entity.", example=None) # No specific entity for manual bonus
    # performed_by_user_id is usually the authenticated user (e.g., an admin performing a manual adjustment).
    # balance_after_transaction is calculated and stored by the system, not part of create/update payload.

class AccountTransactionCreate(AccountTransactionBase):
    """
    Schema for creating a new account transaction (e.g., manual adjustments by an admin).
    `account_id` would typically be specified (e.g., from path or explicit selection).
    `performed_by_user_id` would be the authenticated admin user (set by service).
    """
    account_id: int = Field(..., description="ID of the UserAccount this transaction affects.")
    # Ensure all mandatory fields from AccountTransactionBase are covered or have defaults.
    # transaction_type and amount are mandatory from base.
    pass

# AccountTransactionUpdate is typically not needed as transactions are usually immutable records.
# Adjustments are made by creating new, counter-transactions.

class AccountTransactionResponse(BaseResponseSchema, AccountTransactionBase):
    """
    Schema for representing an account transaction in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    `created_at` effectively serves as the transaction_date.
    """
    # Fields from AccountTransactionBase: transaction_type, amount, description, related_entity_type, related_entity_id
    # Fields from BaseResponseSchema: id, created_at, updated_at

    account: UserAccountBasicInfo = Field(..., description="Basic information about the account affected.")
    performed_by: Optional[UserBasicInfo] = Field(None, description="Basic information about the user who performed/authorized this transaction (if applicable).")
    balance_after_transaction: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="Account balance immediately after this transaction was applied.", example=Decimal("150.00"))


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- AccountTransaction Schemas --- Demonstration")

    # AccountTransactionCreate Example
    # Assume performed_by_user_id=current_admin.id from service/context
    tx_create_data = {
        "accountId": 1, # camelCase for account_id
        "transactionType": TransactionTypeEnum.ADJUSTMENT_CREDIT, # Pass Enum member
        "amount": Decimal("15.25"),
        "description": "Manual correction for Q2 bonus calculation error.",
        "relatedEntityType": "admin_action",
        # "relatedEntityId": 789 # e.g., ID of an admin action log
    }
    try:
        create_schema = AccountTransactionCreate(**tx_create_data) # type: ignore[call-arg]
        logger.info(f"AccountTransactionCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating AccountTransactionCreate: {e}")

    # AccountTransactionResponse Example
    account_info_data = {"id": 1, "currencyName": "Merits", "userId": 101, "groupId": 1}
    admin_user_info_data = {"id": 5, "name": "Super Admin"}

    response_data = {
        "id": 1001, # ID of the AccountTransaction record
        "createdAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "account": account_info_data,
        "transactionType": TransactionTypeEnum.CREDIT_MANUAL_BONUS, # Pass Enum member
        "amount": Decimal("100.00"),
        "balanceAfterTransaction": Decimal("550.75"),
        "description": "Discretionary bonus for outstanding contribution.",
        "performedBy": admin_user_info_data, # camelCase for performed_by
        "relatedEntityType": "manual_bonus_award",
        "relatedEntityId": 32
    }
    try:
        response_schema = AccountTransactionResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"AccountTransactionResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.account and response_schema.performed_by:
            logger.info(f"  Transaction for Account ID: {response_schema.account.id}, Performed by: {response_schema.performed_by.name}")
    except Exception as e:
        logger.error(f"Error creating AccountTransactionResponse: {e}")
