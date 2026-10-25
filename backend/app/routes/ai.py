"""Ask Dukaan AI — grounded Gemini chat."""

from fastapi import APIRouter, HTTPException

from app.dependencies import ActiveShopUser, AppSettings, DBSession
from app.schemas import AIChatRequest, AIChatResponse
from app.services.gemini_service import AIServiceError, generate_reply

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
def chat(
    payload: AIChatRequest,
    user: ActiveShopUser,
    db: DBSession,
    settings: AppSettings,
) -> AIChatResponse:
    try:
        reply, sources, model, provider = generate_reply(
            db=db,
            shop_id=user.shop_id,
            user_id=user.id,
            message=payload.message,
            settings=settings,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return AIChatResponse(reply=reply, sources=sources, model=model, provider=provider)
