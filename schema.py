from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import (
    BaseModel, 
    Field, 
    AliasChoices, 
    field_validator, 
    model_validator
)
from typing_extensions import Self


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    OVERDUE = "OVERDUE"
    UNSPECIFIED = "UNSPECIFIED"


class LineItem(BaseModel):
    description: str = Field(
        ...,
        validation_alias=AliasChoices("description", "item_name", "product_name"),
        description="The standardized description or name of the item or service"
    )
    quantity: float = Field(
        ..., 
        gt=0, 
        description="Quantity ordered, must be strictly greater than 0"
    )
    unit_price: float = Field(
        ..., 
        ge=0, 
        description="Cost per single unit in the specified currency"
    )
    total_price: float = Field(
        ..., 
        ge=0, 
        description="Total cost for this item line. MUST equal quantity * unit_price"
    )

    @model_validator(mode="after")
    def verify_line_math(self) -> Self:
        """
        Enforce that total_price == quantity * unit_price within rounding tolerance.
        If the model hallucinated or mistranscribed, this raises a ValueError.
        Instructor catches it and asks the model to re-multiply.
        """
        expected_total = round(self.quantity * self.unit_price, 2)
        actual_total = round(self.total_price, 2)
        if abs(expected_total - actual_total) > 0.05:
            raise ValueError(
                f"Math error for '{self.description}': total_price ({actual_total}) "
                f"does not match quantity ({self.quantity}) * unit_price ({self.unit_price}) = {expected_total}."
            )
        return self


class PurchaseOrder(BaseModel):
    vendor_name: str = Field(..., description="Company or individual selling the goods")
    buyer_name: Optional[str] = Field(None, description="Purchaser name if specified")
    order_date: Optional[date] = Field(
        None, 
        description="ISO date (YYYY-MM-DD) of the transaction"
    )
    currency: str = Field(
        default="USD", 
        description="Three-letter ISO currency code, e.g., USD, GHS, NGN, EUR"
    )
    items: List[LineItem] = Field(
        ..., 
        min_length=1, 
        description="List of purchased items. Cannot be empty."
    )
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.UNSPECIFIED,
        description=(
            "Current payment state: "
            "PAID if already settled; "
            "PENDING if awaiting payment, unpaid, not settled yet, or on credit; "
            "OVERDUE if late; "
            "UNSPECIFIED if no payment context is given."
        )
    )
    grand_total: float = Field(
        ..., 
        description="The calculated sum of all item total_prices"
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code, received: {clean}")
        return clean

    @model_validator(mode="after")
    def verify_grand_total(self) -> Self:
        """
        Verify that grand_total matches the sum of all individual line items.
        """
        calculated_sum = round(sum(item.total_price for item in self.items), 2)
        if abs(calculated_sum - round(self.grand_total, 2)) > 0.05:
            raise ValueError(
                f"Grand total mismatch: grand_total is {self.grand_total}, "
                f"but sum of line items is {calculated_sum}."
            )
        return self