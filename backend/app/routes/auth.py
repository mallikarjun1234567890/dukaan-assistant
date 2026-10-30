"""Login, logout, CSRF, and current-user endpoints."""

from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import AppSettings, AuthUser, DBSession
from app.models import Shop
from app.schemas import (
    AuthResponse,
    CsrfResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserOut,
)
from app.security import create_access_token, hash_password, new_csrf_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookies(response: Response, token: str, csrf_token: str, settings) -> None:
    max_age = settings.access_token_expire_minutes * 60
    cookie_common = {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        "max_age": max_age,
        "path": "/",
    }
    response.set_cookie(settings.cookie_name, token, **cookie_common)
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response, settings) -> None:
    response.delete_cookie(settings.cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


def user_to_out(user, db) -> UserOut:
    from app.services.subscription import shop_is_locked

    shop = db.get(Shop, user.shop_id) if user.shop_id else None
    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        shop_id=user.shop_id,
        shop_name=shop.name if shop else "",
        owner_name=user.display_name or "",
        avatar_url=user.avatar_url or "",
        plan=shop.plan if shop else "",
        checkout_preference=shop.checkout_preference if shop else "trial",
        shop_locked=shop_is_locked(shop) if shop else False,
        trial_ends_at=shop.trial_ends_at if shop else None,
        grace_ends_at=shop.grace_ends_at if shop else None,
        plan_expires_at=shop.plan_expires_at if shop else None,
        paid_at=shop.paid_at if shop else None,
    )


@router.get("/csrf", response_model=CsrfResponse)
def issue_csrf(response: Response, settings: AppSettings) -> CsrfResponse:
    token = new_csrf_token()
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        httponly=False,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return CsrfResponse(csrf_token=token)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: DBSession,
    settings: AppSettings,
) -> AuthResponse:
    from sqlalchemy import select

    from app.models import User

    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    from app.services.subscription import normalize_plan_preference, start_trial

    shop = Shop(
        name=payload.shop_name,
        phone=payload.phone,
        timezone=settings.shop_timezone,
        opens_at="09:00",
        closes_at="21:30",
        checkout_preference=normalize_plan_preference(payload.plan_preference),
    )
    start_trial(shop)
    db.add(shop)
    db.flush()
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.owner_name,
        role="shop_owner",
        shop_id=shop.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        user_id=user.id, shop_id=user.shop_id, role=user.role, settings=settings
    )
    csrf_token = new_csrf_token()
    _set_auth_cookies(response, access_token, csrf_token, settings)
    from app.services.email_service import deliver, send_welcome

    login_url = f"{settings.frontend_url.rstrip('/')}/login"
    deliver(
        settings,
        lambda: send_welcome(
            settings=settings, to=email, shop_name=shop.name, login_url=login_url
        ),
    )
    return AuthResponse(user=user_to_out(user, db), csrf_token=csrf_token)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: DBSession,
    settings: AppSettings,
) -> AuthResponse:
    from sqlalchemy import select

    from app.models import User

    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=user.id, shop_id=user.shop_id, role=user.role, settings=settings
    )
    csrf_token = new_csrf_token()
    _set_auth_cookies(response, access_token, csrf_token, settings)
    return AuthResponse(user=user_to_out(user, db), csrf_token=csrf_token)


@router.post("/logout")
def logout(response: Response, settings: AppSettings, _user: AuthUser) -> dict[str, str]:
    _clear_auth_cookies(response, settings)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: AuthUser, db: DBSession) -> UserOut:
    return user_to_out(user, db)


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest, db: DBSession, settings: AppSettings
) -> dict[str, str]:
    from sqlalchemy import select

    from app.models import User
    from app.services.email_service import EmailError, configured, send_password_reset
    from app.services.password_reset import issue_reset_token, rate_limiter

    if not configured(settings):
        raise HTTPException(
            status_code=503,
            detail="Password reset email is not configured. Add RESEND_API_KEY to backend/.env.",
        )
    email = str(payload.email).lower()
    if rate_limiter.too_many(email):
        raise HTTPException(status_code=429, detail="Too many reset requests. Try again later.")
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        raw = issue_reset_token(db, user)
        reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw}"
        try:
            send_password_reset(settings=settings, to=user.email, reset_url=reset_url)
        except EmailError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"detail": "If that email is registered, we sent a reset link."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: DBSession) -> dict[str, str]:
    from app.services.password_reset import consume_reset_token

    user = consume_reset_token(db, payload.token)
    if user is None:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {"detail": "Password updated. You can sign in with the new password."}
