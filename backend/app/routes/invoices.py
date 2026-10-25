"""Invoice history and transactional billing."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveShopUser, AppSettings, DBSession
from app.schemas import InvoiceCreate, InvoiceListOut, InvoiceOut
from app.services.invoice_service import (
    InvoiceError,
    create_invoice,
    get_invoice,
    invoice_to_out,
    list_invoices,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=InvoiceListOut)
def list_shop_invoices(user: ActiveShopUser, db: DBSession) -> InvoiceListOut:
    invoices = list_invoices(db, user.shop_id)
    return InvoiceListOut(items=[invoice_to_out(invoice) for invoice in invoices])


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_shop_invoice(invoice_id: int, user: ActiveShopUser, db: DBSession) -> InvoiceOut:
    invoice = get_invoice(db, user.shop_id, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice_to_out(invoice)


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_shop_invoice(
    payload: InvoiceCreate, user: ActiveShopUser, db: DBSession, settings: AppSettings
) -> InvoiceOut:
    try:
        invoice = create_invoice(db, user.shop_id, payload, settings.shop_timezone)
    except InvoiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return invoice_to_out(invoice)
