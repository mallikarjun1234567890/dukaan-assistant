"""Pydantic request and response schemas. Money is exposed in rupees."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator


def normalize_email(value: str) -> str:
    cleaned = value.strip().lower()
    local, separator, domain = cleaned.partition("@")
    if not separator or not local or "." not in domain or " " in cleaned:
        raise ValueError("Enter a valid email address")
    return cleaned


EmailAddress = Annotated[str, AfterValidator(normalize_email)]


class MoneyOut(BaseModel):
    paise: int
    rupees: Decimal
    formatted: str


class LoginRequest(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=8, max_length=200)
    shop_name: str = Field(min_length=2, max_length=200)
    owner_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=8, max_length=30)

    @field_validator("shop_name", "owner_name", "phone")
    @classmethod
    def strip_names(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailAddress
    role: str
    shop_id: int | None = None
    shop_name: str = ""
    owner_name: str = ""
    avatar_url: str = ""
    plan: str = ""
    shop_locked: bool = False
    trial_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None
    plan_expires_at: datetime | None = None
    paid_at: datetime | None = None


class ShopSettingsIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    timezone: str | None = Field(default=None, max_length=64)
    opens_at: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    closes_at: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    weekly_off: str | None = Field(default=None, max_length=20)


class ShopSettingsOut(BaseModel):
    shop_id: int
    name: str
    phone: str
    timezone: str
    opens_at: str
    closes_at: str
    weekly_off: str
    logo_url: str
    plan: str = "trial"
    trial_started_at: datetime | None = None
    trial_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None
    plan_expires_at: datetime | None = None
    paid_at: datetime | None = None
    shop_locked: bool = False
    local_time: str
    weekday: str
    is_open: bool


class AuthResponse(BaseModel):
    user: UserOut
    csrf_token: str


class CsrfResponse(BaseModel):
    csrf_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailAddress


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    selling_price: Decimal = Field(ge=0)
    purchase_cost: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    minimum_stock: int = Field(ge=0)
    supplier_name: str = Field(default="", max_length=200)

    @field_validator("name", "sku", "category")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned

    @field_validator("supplier_name")
    @classmethod
    def strip_supplier(cls, value: str) -> str:
        return value.strip()

    @field_validator("selling_price", "purchase_cost")
    @classmethod
    def two_decimals(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    selling_price: Decimal | None = Field(default=None, ge=0)
    purchase_cost: Decimal | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    minimum_stock: int | None = Field(default=None, ge=0)
    supplier_name: str | None = Field(default=None, max_length=200)

    @field_validator("name", "sku", "category", "supplier_name")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class ProductOut(BaseModel):
    id: int
    shop_id: int
    name: str
    sku: str
    category: str
    selling_price: Decimal
    purchase_cost: Decimal
    selling_price_paise: int
    purchase_cost_paise: int
    stock_quantity: int
    minimum_stock: int
    supplier_name: str
    is_low_stock: bool
    stock_status: Literal["out", "low", "healthy"]
    image_url: str = ""
    created_at: datetime
    updated_at: datetime


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    categories: list[str]


class InvoiceItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class InvoiceCreate(BaseModel):
    items: list[InvoiceItemIn] = Field(min_length=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class InvoiceItemOut(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class InvoiceOut(BaseModel):
    id: int
    shop_id: int
    invoice_number: str
    subtotal: Decimal
    total: Decimal
    subtotal_paise: int
    total_paise: int
    status: str
    created_at: datetime
    items: list[InvoiceItemOut]


class InvoiceListOut(BaseModel):
    items: list[InvoiceOut]


class DashboardRecentInvoice(BaseModel):
    id: int
    invoice_number: str
    total: Decimal
    status: str
    created_at: datetime
    item_count: int


class StockLevelPoint(BaseModel):
    name: str
    stock_quantity: int
    minimum_stock: int
    status: str


class DashboardOut(BaseModel):
    shop_name: str
    local_time: str = ""
    weekday: str = ""
    is_open: bool = True
    opens_at: str = "09:00"
    closes_at: str = "21:30"
    weekly_off: str = ""
    product_count: int
    inventory_value: Decimal
    inventory_value_paise: int
    low_stock_count: int
    out_of_stock_count: int
    today_sales: Decimal
    today_sales_paise: int
    today_invoice_count: int
    recent_invoices: list[DashboardRecentInvoice]
    stock_levels: list[StockLevelPoint]
    stock_summary: dict[str, int]


class ReorderOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    minimum_stock: int
    suggested_quantity: int
    supplier_name: str
    estimated_cost: Decimal
    estimated_cost_paise: int
    status: str
    created_at: datetime
    updated_at: datetime


class ReorderListOut(BaseModel):
    items: list[ReorderOut]
    rule: str


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AIChatResponse(BaseModel):
    reply: str
    sources: list[str] = Field(default_factory=list)
    model: str
    provider: str = "gemini"


class UploadOut(BaseModel):
    url: str
    kind: str


class BillingConfigOut(BaseModel):
    enabled: bool
    key_id: str = ""
    plan: str = "trial"
    amount_rupees: int = 1
    list_price_rupees: int = 499
    trial_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None
    plan_expires_at: datetime | None = None
    paid_at: datetime | None = None
    shop_locked: bool = False


class AdminShopOut(BaseModel):
    id: int
    name: str
    owner_email: str = ""
    phone: str = ""
    plan: str
    trial_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None
    plan_expires_at: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime


class AdminShopListOut(BaseModel):
    items: list[AdminShopOut]


class AdminStatsOut(BaseModel):
    total_shops: int
    trial_count: int
    active_count: int
    expired_count: int
    successful_pays: int
    test_revenue_rupees: int
    list_revenue_rupees: int
    list_price_rupees: int = 499


class BillingOrderOut(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class BillingVerifyIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class HealthOut(BaseModel):
    status: str
    service: str
