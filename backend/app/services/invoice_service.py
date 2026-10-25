"""Transactional invoice creation with backend-owned totals and stock deduction."""

from datetime import datetime

from app.timeutil import shop_zone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import IdempotencyKey, Invoice, InvoiceItem, Product, utc_now
from app.money import paise_to_rupees
from app.schemas import InvoiceCreate, InvoiceItemOut, InvoiceOut


class InvoiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def invoice_to_out(invoice: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=invoice.id,
        shop_id=invoice.shop_id,
        invoice_number=invoice.invoice_number,
        subtotal=paise_to_rupees(invoice.subtotal_paise),
        total=paise_to_rupees(invoice.total_paise),
        subtotal_paise=invoice.subtotal_paise,
        total_paise=invoice.total_paise,
        status=invoice.status,
        created_at=invoice.created_at,
        items=[
            InvoiceItemOut(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name_snapshot,
                quantity=item.quantity,
                unit_price=paise_to_rupees(item.unit_price_paise),
                line_total=paise_to_rupees(item.line_total_paise),
            )
            for item in invoice.items
        ],
    )


def next_invoice_number(db: Session, timezone_name: str) -> str:
    today = datetime.now(shop_zone(timezone_name)).strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    last = db.scalar(
        select(func.max(Invoice.invoice_number)).where(Invoice.invoice_number.like(f"{prefix}%"))
    )
    sequence = 1
    if last:
        try:
            sequence = int(last.rsplit("-", 1)[-1]) + 1
        except ValueError:
            sequence = 1
    return f"{prefix}{sequence:04d}"


def get_existing_idempotent_invoice(db: Session, shop_id: int, key: str) -> Invoice | None:
    record = db.scalar(
        select(IdempotencyKey).where(IdempotencyKey.shop_id == shop_id, IdempotencyKey.key == key)
    )
    if record is None:
        return None
    return db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == record.invoice_id, Invoice.shop_id == shop_id)
    )


def create_invoice(
    db: Session,
    shop_id: int,
    payload: InvoiceCreate,
    timezone_name: str,
) -> Invoice:
    existing = get_existing_idempotent_invoice(db, shop_id, payload.idempotency_key)
    if existing is not None:
        return existing

    merged_qty: dict[int, int] = {}
    for item in payload.items:
        merged_qty[item.product_id] = merged_qty.get(item.product_id, 0) + item.quantity

    product_ids = list(merged_qty.keys())
    products = list(
        db.scalars(
            select(Product).where(Product.shop_id == shop_id, Product.id.in_(product_ids))
        ).all()
    )
    found = {product.id: product for product in products}
    missing = [pid for pid in product_ids if pid not in found]
    if missing:
        raise InvoiceError("One or more products were not found in your shop", 404)

    line_items: list[tuple[Product, int, int]] = []
    subtotal = 0
    for product_id, quantity in merged_qty.items():
        product = found[product_id]
        if quantity <= 0:
            raise InvoiceError("Quantity must be greater than zero")
        if product.stock_quantity < quantity:
            raise InvoiceError(
                f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
        line_total = product.selling_price_paise * quantity
        subtotal += line_total
        line_items.append((product, quantity, line_total))

    invoice = Invoice(
        shop_id=shop_id,
        invoice_number=next_invoice_number(db, timezone_name),
        subtotal_paise=subtotal,
        total_paise=subtotal,
        status="confirmed",
        created_at=utc_now(),
    )
    db.add(invoice)
    db.flush()

    for product, quantity, line_total in line_items:
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                product_name_snapshot=product.name,
                quantity=quantity,
                unit_price_paise=product.selling_price_paise,
                line_total_paise=line_total,
            )
        )
        product.stock_quantity -= quantity
        product.updated_at = utc_now()

    db.add(
        IdempotencyKey(
            shop_id=shop_id,
            key=payload.idempotency_key,
            invoice_id=invoice.id,
        )
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        replay = get_existing_idempotent_invoice(db, shop_id, payload.idempotency_key)
        if replay is not None:
            return replay
        raise InvoiceError("Could not create invoice. Please retry with a new key.") from None

    db.refresh(invoice)
    invoice = db.scalar(
        select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == invoice.id)
    )
    if invoice is None:
        raise InvoiceError("Invoice was created but could not be reloaded", 500)
    return invoice


def list_invoices(db: Session, shop_id: int) -> list[Invoice]:
    return list(
        db.scalars(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.shop_id == shop_id)
            .order_by(Invoice.created_at.desc())
        ).all()
    )


def get_invoice(db: Session, shop_id: int, invoice_id: int) -> Invoice | None:
    return db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice_id, Invoice.shop_id == shop_id)
    )
