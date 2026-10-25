"""Dashboard statistics calculated from SQLite, never hardcoded in the UI."""

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import ActiveShopUser, AppSettings, DBSession
from app.models import Invoice, Product, Shop
from app.money import paise_to_rupees
from app.schemas import DashboardOut, DashboardRecentInvoice, StockLevelPoint
from app.services.inventory_service import inventory_value_paise, is_low_stock, stock_status
from app.shop_hours import shop_clock
from app.timeutil import today_utc_bounds

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(user: ActiveShopUser, db: DBSession, settings: AppSettings) -> DashboardOut:
    shop = db.get(Shop, user.shop_id)
    products = list(db.scalars(select(Product).where(Product.shop_id == user.shop_id)).all())
    zone = (shop.timezone if shop and shop.timezone else settings.shop_timezone)
    start, end = today_utc_bounds(zone)
    clock = shop_clock(shop) if shop else {}

    today_invoices = list(
        db.scalars(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(
                Invoice.shop_id == user.shop_id,
                Invoice.status == "confirmed",
                Invoice.created_at >= start,
                Invoice.created_at < end,
            )
        ).all()
    )
    recent = list(
        db.scalars(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.shop_id == user.shop_id)
            .order_by(Invoice.created_at.desc())
            .limit(6)
        ).all()
    )

    low = [p for p in products if is_low_stock(p.stock_quantity, p.minimum_stock)]
    out = [p for p in products if p.stock_quantity <= 0]
    healthy = [p for p in products if stock_status(p.stock_quantity, p.minimum_stock) == "healthy"]
    value = inventory_value_paise(products)
    today_sales = sum(inv.total_paise for inv in today_invoices)

    stock_levels = [
        StockLevelPoint(
            name=product.name,
            stock_quantity=product.stock_quantity,
            minimum_stock=product.minimum_stock,
            status=stock_status(product.stock_quantity, product.minimum_stock),
        )
        for product in sorted(products, key=lambda p: p.stock_quantity)[:10]
    ]

    return DashboardOut(
        shop_name=shop.name if shop else "",
        local_time=str(clock.get("local_time", "")),
        weekday=str(clock.get("weekday", "")),
        is_open=bool(clock.get("is_open", True)),
        opens_at=str(clock.get("opens_at", "09:00")),
        closes_at=str(clock.get("closes_at", "21:30")),
        weekly_off=str(clock.get("weekly_off", "")),
        product_count=len(products),
        inventory_value=paise_to_rupees(value),
        inventory_value_paise=value,
        low_stock_count=len(low),
        out_of_stock_count=len(out),
        today_sales=paise_to_rupees(today_sales),
        today_sales_paise=today_sales,
        today_invoice_count=len(today_invoices),
        recent_invoices=[
            DashboardRecentInvoice(
                id=inv.id,
                invoice_number=inv.invoice_number,
                total=paise_to_rupees(inv.total_paise),
                status=inv.status,
                created_at=inv.created_at,
                item_count=len(inv.items),
            )
            for inv in recent
        ],
        stock_levels=stock_levels,
        stock_summary={"healthy": len(healthy), "low": len(low), "out": len(out)},
    )
