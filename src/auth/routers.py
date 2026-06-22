from dataclasses import dataclass

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)
from starlette.datastructures import Address

from core.security.jwt.schams import TokenPair

from .controller import AuthController
from .dependencies import get_auth_controller
from .schamas import (
    LoginSchema,
    RegisterAccessSchema,
    RegisterRefreshSchema,
    logoutSchamas,
)

router = APIRouter(
    prefix="/auth",
)


@router.post("/login", response_model=TokenPair)
async def login(
    login_data: LoginSchema,
    request: Request,
    response: Response,
    auth_controller: AuthController = Depends(get_auth_controller),
):

    @dataclass(frozen=True)
    class RequestContext:
        """
        Represents the context of a request, including the user agent and IP address.
        and prevent that coppeling between the request and the controller.
        and eliminate and limited that coupling to the request object. and more Meta data
        """

        user_agent: str
        ip_address: Address

    request_context = RequestContext(
        user_agent=request.headers.get("user-agent", ""),
        ip_address=Address(host=request.client.host, port=request.client.port),
    )

    result = await auth_controller.login(
        login_data, context={"request": request_context}
    )
    return result


@router.post("/register-access")
async def register_access(
    request: Request,
    response: Response,
    data: RegisterAccessSchema,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    result = await auth_controller.register_access(
        data=data, request=request, response=response
    )
    return result.model_dump()


@router.post("/register-refresh")
async def register_refresh(
    request: Request,
    response: Response,
    data: RegisterRefreshSchema,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    result, family_id = await auth_controller.register_refresh(
        data=data, request=request, response=response
    )
    return {**result.model_dump(), "family_id": family_id}


@router.post("/refresh")
async def refresh(
    data: RegisterRefreshSchema,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    access_token, family_id = await auth_controller.refresh(data=data)
    return {
        **RegisterAccessSchema(access_token=access_token).model_dump(),
        "family_id": family_id,
    }


@router.post("/logout")
async def logout(
    logoutSchamas: logoutSchamas,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    if await auth_controller.logout(data=logoutSchamas):
        return {"message": "Logged out successfully"}
    else:
        return {"message": "Logout failed"}
