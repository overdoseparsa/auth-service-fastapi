# token_service.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import ValidationError

from core.config import settings
from core.security.utils.token_utils import generate_token

from .exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TypeTokenError,
)
from .schams import (
    DecodedAccessToken,
    DecodedRefreshToken,
    EncodedAccessToken,
    EncodedRefreshToken,
)
from .utils import (
    _utc_now as _utc_now_utils,
)
from .utils import (
    convert_datetime_timestamp as convert_datetime_timestamp_utils,
)
from .utils import (
    convert_timestamp_datetime as convert_timestamp_datetime_utils,
)


class TokenService:
    @staticmethod
    def _utc_now() -> datetime:
        "returns the current UTC datetime"
        return _utc_now_utils()

    @staticmethod
    def convert_datetime_timestamp(dt: datetime) -> float:
        "for converting a datetime to a Unix timestamp"
        return convert_datetime_timestamp_utils(dt)

    @staticmethod
    def convert_timestamp_datetime(ts: float) -> datetime:
        "for converting a Unix timestamp to a datetime"
        return datetime.fromtimestamp(ts, timezone.utc)

    def create_jti_token(self) -> str:
        "create a unique identifier for the token"
        return generate_token()

    """
    Production-oriented token service.

    Design:
    - Access token: stateless JWT, short TTL
    - Refresh token: JWT + persisted jti for rotation/revocation/reuse detection


    Requirements:
        sub: if that subject from the user ID or role or many other factors
        jti: unique identifier for the token
        iat: issued at timestamp
        nbf: not before timestamp
        exp: expiration timestamp
        iss: issuer :
            the issuer of the token, typically the authentication service like >>> auth.example.com
            who created this token ?



        aud: audience :
            this token is intended for for witch recipient or client or service


            "payload": {
              "iss": "https://auth.logto.io",
              "sub": "test_user",
              "aud": "auth_service",
              "exp": 1516239022,
              "iat": 1516239022,
              "username": "foo"
            },
            but my service is walllet
            so i need to verify that the token is intended for my service
            and it will reject any token that is not intended for my service

        type: token type (access or refresh)
        family id last refresh token that was create by

    this layer just that service for Token Creation or decode

    """

    def __init__(
        self,
        *,
        audience: str,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.JWT_ALGORITHM,
        issuer: str = settings.ISSUER,
        access_ttl: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_ttl: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        utc_now: Callable[[], datetime] | None = None,
        convert_datetime_timestamp: Callable[[datetime], float] | None = None,
        convert_timestamp_datetime: Callable[[float], datetime] | None = None,
        token_generator: Callable[[], str] | None = None,
    ) -> None:

        if not audience:
            raise ValueError("audience must not be empty")

        "secret_key : the secret key used to sign the token"
        self.secret_key: str = secret_key

        "algorithm : the algorithm used to sign the token"
        self.algorithm: str = algorithm

        "issuer : the issuer of the token"
        self.issuer: str = issuer

        "audience : the audience of the token"
        self.audience: str = audience

        "access_ttl : the time to live for the access token"
        self.access_ttl: timedelta = access_ttl

        "refresh_ttl : the time to live for the refresh token"
        self.refresh_ttl: timedelta = refresh_ttl

        "utc_now : the function to get the current UTC datetime"
        self.utc_now: Callable[[], datetime] = utc_now or self._utc_now

        "convert_datetime_timestamp : the function to convert a datetime to a Unix timestamp"
        self.convert_datetime_timestamp: Callable[[datetime], float] = (
            convert_datetime_timestamp or TokenService.convert_datetime_timestamp
        )

        "convert_timestamp_datetime : the function to convert a Unix timestamp to a datetime"
        self.convert_timestamp_datetime: Callable[[float], datetime] = (
            convert_timestamp_datetime or TokenService.convert_timestamp_datetime
        )

        "token_generator : the function to generate a JTI token"
        self.token_generator: Callable[[], str] = (
            token_generator or self.create_jti_token
        )

    def _base_claims(
        self,
        *,
        token_type: str,
        subject: str,
        now: datetime,
        ttl: timedelta,
        nbf: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Returns the base claims for a token.
        base claims are the common claims that are included in all tokens.
        such as refresh token and access token. this is common across all tokens.

        >>> data = {
            'sub': 'user_id:1',
            'jti': '', # unique token id from each token
            'type': 'access', # or 'refresh'
            'iat': 0,
            'nbf': 0,
            'exp': 0,
            'iss': '',
            'aud': '',
        }

        """

        return {
            "sub": subject,
            "jti": self.token_generator(),  # must unique for each token
            "type": token_type,
            "iat": self.convert_datetime_timestamp(now),
            "nbf": self.convert_datetime_timestamp(now)
            if not nbf
            else self.convert_datetime_timestamp(now + nbf),
            "exp": self.convert_datetime_timestamp(now + ttl),
            "iss": self.issuer,
            "aud": self.audience,
        }

    def _encode(self, payload: dict[str, Any]) -> str:
        "encode from pyload to JWT token can be access or refresh token"
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def _decode(
        self, token: str, return_dict: bool = False
    ) -> DecodedAccessToken | DecodedRefreshToken | dict[str, Any]:
        """
        Decode JWT token to access or refresh token and return the decoded token.
        return the decoded token as a DecodedAccessToken or DecodedRefreshToken instance.

        >>> token_object = TokenService(...)
        >>> data = token_object._decode(token="your-token")
        >>> data
        if access token:
        DecodedAccessToken(type='access', sub='',...)
        if refresh token:
        DecodedRefreshToken(type='refresh', sub='',...)


        data.type  # 'access' or 'refresh'
        """
        try:
            token: dict[str, Any] = jwt.decode(
                token=token,
                key=self.secret_key,
                algorithms=self.algorithm,
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "aud", "iss", "sub", "type"]},
            )

            if token.get("type") == "access":
                try:
                    return (
                        DecodedAccessToken(**token)
                        if not return_dict
                        else DecodedAccessToken(**token).model_dump()
                    )
                except ValidationError:
                    raise InvalidTokenError("Invalid access token")
            elif token.get("type") == "refresh":
                try:
                    return (
                        DecodedRefreshToken(**token)
                        if not return_dict
                        else DecodedRefreshToken(**token).model_dump()
                    )
                except ValidationError as exc:
                    raise InvalidTokenError(f"Invalid refresh token {exc}") from exc
            else:
                raise TypeTokenError("Token type is invalid")

        except ExpiredSignatureError as exc:
            raise TokenExpiredError(f"Token has expired {exc}") from exc
        except JWTError as exc:
            raise InvalidTokenError(f"Invalid token {exc}") from exc

    def create_access_token(
        self, *, user_id: str, extra_claims: dict[str, Any] | None = None
    ) -> tuple[str, EncodedAccessToken]:
        """
        Creates an access token for the given user and role.

        Args:
            user_id (str): The user ID.
            role (str): The user role.
            extra_claims (dict[str, Any] | None): Extra claims to include in the token.

        Returns:
            str: The encoded access token.

            self.utc_now must be callable to override the default UTC now function.
            def _utc_now() -> datetime:
                return datetime.now(timezone.utc)

            now: datetime = self.utc_now()

        """

        now: datetime = self._utc_now()

        payload = self._base_claims(
            token_type="access",
            subject=str(user_id),
            now=now,
            ttl=self.access_ttl,
        )
        if extra_claims:
            payload.update(extra_claims)

        return self._encode(payload), EncodedAccessToken(**payload)

    def create_refresh_token(
        self,
        *,
        user_id: int,
        extra_claims: dict[str, Any] | None = None,
    ) -> tuple[str, EncodedRefreshToken]:
        "create just refresh token"

        now = self._utc_now()

        payload = self._base_claims(
            token_type="refresh",
            subject=str(user_id),
            now=now,
            ttl=self.refresh_ttl,
        )

        if extra_claims:
            payload.update(extra_claims)

        token = self._encode(payload)

        print("Pyload is ", payload)
        return token, EncodedRefreshToken(**payload)

    def decode_access_token(self, token: str) -> DecodedAccessToken:
        token = self._decode(token)
        return token

    def decode_refresh_token(self, token: str) -> DecodedRefreshToken:
        token = self._decode(token)
        return token
