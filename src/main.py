import uvicorn
from fastapi.responses import JSONResponse
from fastapi_offline import FastAPIOffline as FastAPI

from auth.routers import router as auth_router
from core.base.expections import CustomException
from core.config import settings
from infrastructure.sqlalchemy.utiles import init_models
from users.router import router as users_router


async def create_models(app: FastAPI):
    await init_models()
    # TODO check that Connections Befors StartUP app 
    yield
    # Close Connection After Complete Close ... 





app = FastAPI(lifespan=create_models)


app.include_router(router=users_router, tags=["Users"])
app.include_router(router=auth_router, tags=["Auth"])


@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "status_code": exc.code,
            },
        },
    )


from core.config import settings


def main():
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.POST,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )


if __name__ == "__main__":
    main()
