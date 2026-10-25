"""Deterministic reorder recommendations scoped to the authorized shop."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, ReorderRequest, utc_now
from app.money import paise_to_rupees
from app.schemas import ReorderOut
from app.services.inventory_service import is_low_stock, suggested_reorder_quantity

REORDER_RULE = (
    "Suggested quantity = max(0, (2 × minimum stock) − current stock). "
    "Approval only records an internal request; it does not contact a supplier or take payment."
)


class ReorderError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def reorder_to_out(request: ReorderRequest, product: Product) -> ReorderOut:
    return ReorderOut(
        id=request.id,
        product_id=product.id,
        product_name=product.name,
        sku=product.sku,
        current_stock=product.stock_quantity,
        minimum_stock=product.minimum_stock,
        suggested_quantity=request.suggested_quantity,
        supplier_name=product.supplier_name,
        estimated_cost=paise_to_rupees(request.estimated_cost_paise),
        estimated_cost_paise=request.estimated_cost_paise,
        status=request.status,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def _estimate_cost(product: Product, quantity: int) -> int:
    return product.purchase_cost_paise * quantity


def sync_recommendations(db: Session, shop_id: int) -> list[ReorderRequest]:
    products = list(db.scalars(select(Product).where(Product.shop_id == shop_id)).all())
    existing_rows = list(
        db.scalars(
            select(ReorderRequest)
            .options(selectinload(ReorderRequest.product))
            .where(ReorderRequest.shop_id == shop_id)
        ).all()
    )
    pending_by_product = {row.product_id: row for row in existing_rows if row.status == "pending"}
    approved_products = {row.product_id for row in existing_rows if row.status == "approved"}

    for product in products:
        if not is_low_stock(product.stock_quantity, product.minimum_stock):
            continue
        quantity = suggested_reorder_quantity(product.stock_quantity, product.minimum_stock)
        if quantity <= 0:
            continue
        existing = pending_by_product.get(product.id)
        if existing:
            existing.suggested_quantity = quantity
            existing.estimated_cost_paise = _estimate_cost(product, quantity)
            existing.updated_at = utc_now()
            continue
        if product.id in approved_products:
            continue
        db.add(
            ReorderRequest(
                shop_id=shop_id,
                product_id=product.id,
                suggested_quantity=quantity,
                estimated_cost_paise=_estimate_cost(product, quantity),
                status="pending",
            )
        )

    db.commit()
    return list(
        db.scalars(
            select(ReorderRequest)
            .options(selectinload(ReorderRequest.product))
            .where(ReorderRequest.shop_id == shop_id)
            .order_by(ReorderRequest.status.asc(), ReorderRequest.updated_at.desc())
        ).all()
    )


def get_shop_reorder(db: Session, shop_id: int, reorder_id: int) -> ReorderRequest | None:
    return db.scalar(
        select(ReorderRequest)
        .options(selectinload(ReorderRequest.product))
        .where(ReorderRequest.id == reorder_id, ReorderRequest.shop_id == shop_id)
    )


def set_status(db: Session, request: ReorderRequest, status: str) -> ReorderRequest:
    if request.status != "pending":
        raise ReorderError("This recommendation has already been actioned")
    request.status = status
    request.updated_at = utc_now()
    db.commit()
    db.refresh(request)
    return request
