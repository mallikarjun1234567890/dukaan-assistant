"""Shop-scoped product CRUD."""

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import ActiveShopUser, DBSession
from app.schemas import ProductCreate, ProductListOut, ProductOut, ProductUpdate
from app.services import inventory_service as inventory

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListOut)
def list_products(
    user: ActiveShopUser,
    db: DBSession,
    search: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None, max_length=80),
    stock_status: str | None = Query(default=None, pattern="^(low|out|healthy)$"),
) -> ProductListOut:
    products = inventory.list_products(
        db, user.shop_id, search=search, category=category, stock_filter=stock_status
    )
    return ProductListOut(
        items=[inventory.product_to_out(product) for product in products],
        total=len(products),
        categories=inventory.unique_categories(db, user.shop_id),
    )


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, user: ActiveShopUser, db: DBSession) -> ProductOut:
    try:
        product = inventory.create_product(db, user.shop_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return inventory.product_to_out(product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, user: ActiveShopUser, db: DBSession) -> ProductOut:
    product = inventory.get_product_for_shop(db, user.shop_id, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return inventory.product_to_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, payload: ProductUpdate, user: ActiveShopUser, db: DBSession
) -> ProductOut:
    product = inventory.get_product_for_shop(db, user.shop_id, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    try:
        product = inventory.update_product(db, product, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return inventory.product_to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, user: ActiveShopUser, db: DBSession) -> None:
    product = inventory.get_product_for_shop(db, user.shop_id, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    inventory.delete_product(db, product)
