import re

from pydantic import BaseModel, Field, field_validator

_PHONE = re.compile(r"^\+998\d{9}$")


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        digits = "998" + digits
    phone = "+" + digits
    if not _PHONE.match(phone):
        raise ValueError("Telefon raqam +998XXXXXXXXX formatida bo'lishi kerak")
    return phone


class RegisterIn(BaseModel):
    phone: str
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(default="", max_length=100)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class LoginIn(BaseModel):
    phone: str
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, max_length=6)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class RefreshIn(BaseModel):
    refresh_token: str | None = None


class TelegramWebAppIn(BaseModel):
    init_data: str = Field(min_length=10, max_length=4096)


class UserOut(BaseModel):
    id: str
    phone: str | None
    email: str | None
    first_name: str
    last_name: str
    telegram_username: str | None
    role: str
    plan_credits: int

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TelegramLoginInitOut(BaseModel):
    token: str
    bot_url: str
    expires_in: int


class TelegramLoginPollOut(BaseModel):
    status: str  # pending | expired | authenticated
    session: TokenOut | None = None
