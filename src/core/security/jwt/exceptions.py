from core.base.expections import CustomException


class TokenError(CustomException):
    """Base token error."""


class InvalidTokenError(TokenError):
    """Token is malformed, invalid signature, or cannot be decoded."""


class TokenExpiredError(TokenError):
    """Token has expired."""


class TypeTokenError(TokenError):
    """Token type is invalid for this operation."""


class TokenMissingClaimError(TokenError):
    """Required token claim is missing."""


class TokenReplayError(TokenError):
    """Refresh token reuse detected."""


class TokenRevokedError(TokenError):
    """Refresh token was revoked."""


class TokenCompromisedError(TokenError):
    """Token family/session marked as compromised."""


class MustNotImplementError(CustomException):
    """Method must not be implemented."""
