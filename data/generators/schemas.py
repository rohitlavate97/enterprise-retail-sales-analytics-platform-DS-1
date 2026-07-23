"""Pydantic data schemas for relational retail analytics dataset.

Defines strongly-typed entity schemas for customers, products, categories, stores,
regions, payment methods, time dimension, transactions, returns, discounts, and shipping.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


class CategorySchema(BaseModel):
    """Product Category entity schema."""

    category_id: str = Field(..., description="Unique category identifier, e.g. CAT-001")
    category_name: str = Field(..., description="Category name (e.g., Electronics, Apparel)")
    department: str = Field(..., description="High-level retail department")


class ProductSchema(BaseModel):
    """Product entity schema."""

    product_id: str = Field(..., description="Unique product identifier, e.g. PRD-1001")
    product_name: str = Field(..., description="Descriptive product title")
    category_id: str = Field(..., description="Foreign key referencing CategorySchema.category_id")
    cost_price: PositiveFloat = Field(..., description="Base manufacturing/procurement cost")
    unit_price: PositiveFloat = Field(..., description="Retail selling price")
    popularity_score: float = Field(..., ge=0.0, le=1.0, description="Pareto popularity weight")


class RegionSchema(BaseModel):
    """Geographic Region entity schema."""

    region_id: str = Field(..., description="Unique region identifier, e.g. REG-NORTH")
    region_name: str = Field(..., description="Region title (North, South, East, West, Central)")
    country: str = Field(default="USA", description="Country name")
    manager_name: str = Field(..., description="Regional manager name")


class StoreSchema(BaseModel):
    """Retail Store entity schema."""

    store_id: str = Field(..., description="Unique store identifier, e.g. STR-05")
    store_name: str = Field(..., description="Store outlet name")
    region_id: str = Field(..., description="Foreign key referencing RegionSchema.region_id")
    store_type: Literal["Superstore", "Express", "Flagship", "Online"] = Field(
        ..., description="Store operational format"
    )
    sqft_area: PositiveInt = Field(..., description="Floor space area in square feet")


class CustomerSchema(BaseModel):
    """Customer entity schema."""

    customer_id: str = Field(..., description="Unique customer identifier, e.g. CUST-0001")
    name: str = Field(..., description="Full customer name")
    email: str = Field(..., description="Customer email address")
    segment: Literal["Consumer", "Corporate", "Home Office"] = Field(
        ..., description="Customer market segment"
    )
    region_id: str = Field(..., description="Foreign key referencing RegionSchema.region_id")
    signup_date: date = Field(..., description="Account creation date")
    churn_risk_score: float = Field(..., ge=0.0, le=1.0, description="Statistical churn risk")


class PaymentMethodSchema(BaseModel):
    """Payment Method entity schema."""

    payment_method_id: str = Field(..., description="Unique payment method key")
    method_name: Literal["Credit Card", "Debit Card", "PayPal", "Cash", "UPI"] = Field(...)


class TimeDimensionSchema(BaseModel):
    """Time Dimension calendar entity schema."""

    date_key: int = Field(..., description="Integer date key in YYYYMMDD format")
    full_date: date = Field(..., description="Standard calendar date")
    year: int = Field(..., ge=2000, le=2100)
    quarter: int = Field(..., ge=1, le=4)
    month: int = Field(..., ge=1, le=12)
    month_name: str = Field(...)
    week_of_year: int = Field(..., ge=1, le=53)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: bool = Field(...)
    is_holiday: bool = Field(...)


class OrderSchema(BaseModel):
    """Order Transaction entity schema."""

    order_id: str = Field(..., description="Unique transaction ID, e.g. ORD-1000001")
    customer_id: str = Field(..., description="FK -> CustomerSchema.customer_id")
    product_id: str = Field(..., description="FK -> ProductSchema.product_id")
    store_id: str = Field(..., description="FK -> StoreSchema.store_id")
    date_key: int = Field(..., description="FK -> TimeDimensionSchema.date_key")
    quantity: PositiveInt = Field(..., description="Number of units purchased")
    unit_price: PositiveFloat = Field(..., description="Selling price per unit")
    discount_amount: float = Field(default=0.0, ge=0.0, description="Total discount deducted")
    total_amount: PositiveFloat = Field(..., description="Final gross line total")
    cost_amount: PositiveFloat = Field(..., description="Cost price multiplied by quantity")
    profit_amount: float = Field(..., description="Net margin (total_amount - cost_amount)")
    payment_method_id: str = Field(..., description="FK -> PaymentMethodSchema.payment_method_id")


class ReturnSchema(BaseModel):
    """Order Return entity schema."""

    return_id: str = Field(..., description="Unique return ticket ID")
    order_id: str = Field(..., description="FK -> OrderSchema.order_id")
    return_date: date = Field(...)
    return_reason: Literal["Defective", "Wrong Item", "Changed Mind", "Size Issue", "Late Delivery"]
    refund_amount: PositiveFloat = Field(...)


class DiscountSchema(BaseModel):
    """Discount Promotion entity schema."""

    discount_id: str = Field(...)
    order_id: str = Field(..., description="FK -> OrderSchema.order_id")
    promo_code: str = Field(...)
    discount_percent: float = Field(..., ge=0.0, le=1.0)


class ShippingSchema(BaseModel):
    """Shipping Logistics entity schema."""

    shipping_id: str = Field(...)
    order_id: str = Field(..., description="FK -> OrderSchema.order_id")
    shipping_mode: Literal["Standard", "Second Day", "Express", "Same Day"]
    shipping_cost: float = Field(..., ge=0.0)
    carrier: str = Field(...)
    is_delayed: bool = Field(default=False)
