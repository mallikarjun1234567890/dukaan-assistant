"""Deterministic inventory calculations. Do not use Gemini for these figures."""

from collections.abc import Iterable

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product, utc_now
from app.money import paise_to_rupees, rupees_to_paise
from app.schemas import ProductCreate, ProductOut, ProductUpdate


def is_low_stock(stock_quantity: int, minimum_stock: int) -> bool:
    return stock_quantity <= minimum_stock


def stock_status(stock_quantity: int, minimum_stock: int) -> str:
    if stock_quantity <= 0:
        return "out"
    if is_low_stock(stock_quantity, minimum_stock):
        return "low"
    return "healthy"


def suggested_reorder_quantity(stock_quantity: int, minimum_stock: int) -> int:
    """Target stock is twice the minimum threshold."""
    target = minimum_stock * 2
    return max(0, target - stock_quantity)


def inventory_value_paise(products: Iterable[Product]) -> int:
    return sum(product.stock_quantity * product.purchase_cost_paise for product in products)


def product_to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        shop_id=product.shop_id,
        name=product.name,
        sku=product.sku,
        category=product.category,
        selling_price=paise_to_rupees(product.selling_price_paise),
        purchase_cost=paise_to_rupees(product.purchase_cost_paise),
        selling_price_paise=product.selling_price_paise,
        purchase_cost_paise=product.purchase_cost_paise,
        stock_quantity=product.stock_quantity,
        minimum_stock=product.minimum_stock,
        supplier_name=product.supplier_name,
        is_low_stock=is_low_stock(product.stock_quantity, product.minimum_stock),
        stock_status=stock_status(product.stock_quantity, product.minimum_stock),
        image_url=product.image_url or "",
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def shop_products_query(shop_id: int) -> Select[tuple[Product]]:
    return select(Product).where(Product.shop_id == shop_id)


def list_products(
    db: Session,
    shop_id: int,
    *,
    search: str | None = None,
    category: str | None = None,
    stock_filter: str | None = None,
) -> list[Product]:
    stmt = shop_products_query(shop_id).order_by(Product.name.asc())
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category:
        stmt = stmt.where(Product.category == category)
    products = list(db.scalars(stmt).all())
    if stock_filter == "low":
        products = [p for p in products if is_low_stock(p.stock_quantity, p.minimum_stock)]
    elif stock_filter == "out":
        products = [p for p in products if p.stock_quantity <= 0]
    elif stock_filter == "healthy":
        products = [p for p in products if stock_status(p.stock_quantity, p.minimum_stock) == "healthy"]
    return products


def get_product_for_shop(db: Session, shop_id: int, product_id: int) -> Product | None:
    return db.scalar(
        select(Product).where(Product.id == product_id, Product.shop_id == shop_id)
    )


def create_product(db: Session, shop_id: int, payload: ProductCreate) -> Product:
    product = Product(
        shop_id=shop_id,
        name=payload.name,
        sku=payload.sku,
        category=payload.category,
        selling_price_paise=rupees_to_paise(payload.selling_price),
        purchase_cost_paise=rupees_to_paise(payload.purchase_cost),
        stock_quantity=payload.stock_quantity,
        minimum_stock=payload.minimum_stock,
        supplier_name=payload.supplier_name,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("A product with this SKU already exists in your shop") from None
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    data = payload.model_dump(exclude_unset=True)
    if "selling_price" in data and data["selling_price"] is not None:
        product.selling_price_paise = rupees_to_paise(data.pop("selling_price"))
    if "purchase_cost" in data and data["purchase_cost"] is not None:
        product.purchase_cost_paise = rupees_to_paise(data.pop("purchase_cost"))
    for field, value in data.items():
        setattr(product, field, value)
    product.updated_at = utc_now()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("A product with this SKU already exists in your shop") from None
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()


def unique_categories(db: Session, shop_id: int) -> list[str]:
    rows = db.scalars(
        select(Product.category).where(Product.shop_id == shop_id).distinct().order_by(Product.category)
    ).all()
    return list(rows)
