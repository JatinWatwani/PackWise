from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI

class PackWiseException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

def register_error_handlers(app: FastAPI):
    @app.exception_handler(PackWiseException)
    async def packwise_exception_handler(request: Request, exc: PackWiseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
