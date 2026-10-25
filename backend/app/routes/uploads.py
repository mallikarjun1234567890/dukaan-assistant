"""Authenticated image uploads via Cloudinary."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.dependencies import ActiveShopUser, AppSettings, DBSession
from app.models import Product, Shop, User
from app.schemas import UploadOut
from app.services.cloudinary_service import UploadError, upload_image

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadOut)
async def upload(
    user: ActiveShopUser,
    db: DBSession,
    settings: AppSettings,
    file: UploadFile = File(...),
    kind: str = Form(...),
    product_id: int | None = Form(default=None),
) -> UploadOut:
    if kind not in {"product", "shop_logo", "avatar"}:
        raise HTTPException(status_code=400, detail="kind must be product, shop_logo, or avatar")
    if kind == "product" and not product_id:
        raise HTTPException(status_code=400, detail="product_id is required for product images")

    folder = f"dukaan/shop-{user.shop_id}/{kind}"
    try:
        url = upload_image(
            settings=settings,
            file_obj=file.file,
            content_type=file.content_type or "",
            folder=folder,
        )
    except UploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if kind == "shop_logo":
        shop = db.get(Shop, user.shop_id)
        if shop:
            shop.logo_url = url
            db.commit()
    elif kind == "avatar":
        owner = db.get(User, user.id)
        if owner:
            owner.avatar_url = url
            db.commit()
    else:
        product = db.get(Product, product_id)
        if product is None or product.shop_id != user.shop_id:
            raise HTTPException(status_code=404, detail="Product not found")
        product.image_url = url
        db.commit()

    return UploadOut(url=url, kind=kind)
