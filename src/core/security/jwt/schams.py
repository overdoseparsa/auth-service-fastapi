from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

TokenType = Literal["access", "refresh"]


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class BaseToken(BaseModel):
    sub: str
    jti: str
    iat: float
    nbf: float
    exp: float
    iss: str
    aud: str


class DecodedAccessToken(BaseToken):
    type: Literal["access"]


class DecodedRefreshToken(BaseToken):
    type: Literal["refresh"]


class EncodedAccessToken(BaseToken):
    type: Literal["access"]


class EncodedRefreshToken(BaseToken):
    type: Literal["refresh"]


class RefreshTokenRecord(BaseModel):
    jti: str
    user_id: str
    family_id: Optional[str]
    expires_at: datetime
    issued_at: datetime
    rotated_from: Optional[str] = None
    revoked_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    compromised: bool = False

    model_config = ConfigDict(frozen=False)


class RefreshTokenBase(BaseModel):
    jti: str
    user_id: int
    family_id: Optional[str]
    expires_at: datetime
    issued_at: datetime
    rotated_from: Optional[str] = None
    revoked_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    compromised: bool = False


class RefreshTokenCreate(RefreshTokenBase, extra="forbid"):
    model_config = ConfigDict(frozen=False)


class RefreshTokenUpdate(RefreshTokenBase, extra="forbid"):
    model_config = ConfigDict(frozen=False)

    jti: Optional[str] = None
    user_id: Optional[str] = None
    family_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    rotated_from: Optional[str] = None
    revoked_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    compromised: Optional[bool] = None
