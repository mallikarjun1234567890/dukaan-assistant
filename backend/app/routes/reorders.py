"""Internal reorder recommendations."""

from fastapi import APIRouter, HTTPException

from app.dependencies import ActiveShopUser, DBSession
from app.schemas import ReorderListOut, ReorderOut
from app.services.reorder_service import (
    REORDER_RULE,
    ReorderError,
    get_shop_reorder,
    reorder_to_out,
    set_status,
    sync_recommendations,
)

router = APIRouter(prefix="/api/reorders", tags=["reorders"])


@router.get("", response_model=ReorderListOut)
def list_reorders(user: ActiveShopUser, db: DBSession) -> ReorderListOut:
    rows = sync_recommendations(db, user.shop_id)
    return ReorderListOut(
        items=[reorder_to_out(row, row.product) for row in rows if row.product is not None],
        rule=REORDER_RULE,
    )


@router.post("/{reorder_id}/approve", response_model=ReorderOut)
def approve_reorder(reorder_id: int, user: ActiveShopUser, db: DBSession) -> ReorderOut:
    request = get_shop_reorder(db, user.shop_id, reorder_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Reorder recommendation not found")
    try:
        request = set_status(db, request, "approved")
    except ReorderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return reorder_to_out(request, request.product)


@router.post("/{reorder_id}/reject", response_model=ReorderOut)
def reject_reorder(reorder_id: int, user: ActiveShopUser, db: DBSession) -> ReorderOut:
    request = get_shop_reorder(db, user.shop_id, reorder_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Reorder recommendation not found")
    try:
        request = set_status(db, request, "rejected")
    except ReorderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return reorder_to_out(request, request.product)
