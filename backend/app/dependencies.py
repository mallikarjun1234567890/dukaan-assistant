"""FastAPI dependencies for authentication, CSRF, and shop authorization."""

from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import User
from app.security import csrf_tokens_match, decode_access_token

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def settings_dep() -> Settings:
    return get_settings()


def get_token_from_request(
    request: Request,
    settings: Settings,
    authorization: str | None,
) -> str | None:
    cookie_token = request.cookies.get(settings.cookie_name)
    if cookie_token:
        return cookie_token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_csrf(
    request: Request,
    settings: Settings,
    csrf_header: str | None,
) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie_csrf = request.cookies.get(settings.csrf_cookie_name)
    if not csrf_tokens_match(cookie_csrf, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    authorization: Annotated[str | None, Header()] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> User:
    token = get_token_from_request(request, settings, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token, settings)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from None

    # Cookie-authenticated mutations need CSRF. Bearer-only clients skip the cookie check.
    if request.cookies.get(settings.cookie_name):
        require_csrf(request, settings, csrf_header)

    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from None

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is no longer valid",
        )

    token_shop = payload.get("shop_id")
    if token_shop != user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    if user.role == "shop_owner" and user.shop_id:
        from app.models import Shop
        from app.services.subscription import sync_shop_plan

        shop = db.get(Shop, user.shop_id)
        if shop is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is no longer valid",
            )
        if sync_shop_plan(db, shop) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is no longer valid",
            )
    return user


def require_shop_owner(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "shop_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    if not user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No shop is associated with this account",
        )
    return user


def require_shop_access(
    user: Annotated[User, Depends(require_shop_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    from app.models import Shop
    from app.services.subscription import SHOP_LOCKED_DETAIL, shop_has_access

    shop = db.get(Shop, user.shop_id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No shop is associated with this account",
        )
    if not shop_has_access(shop):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=SHOP_LOCKED_DETAIL,
        )
    return user


def require_platform_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return user


AuthUser = Annotated[User, Depends(get_current_user)]
CurrentUser = Annotated[User, Depends(require_shop_owner)]
ActiveShopUser = Annotated[User, Depends(require_shop_access)]
PlatformAdmin = Annotated[User, Depends(require_platform_admin)]
DBSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(settings_dep)]
