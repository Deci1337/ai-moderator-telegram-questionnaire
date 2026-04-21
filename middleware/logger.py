from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config.database import async_session_maker
from models.request_log import RequestLog


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/favicon.ico":
            return await call_next(request)

        # Log request
        async with async_session_maker() as session:
            try:
                log_entry = RequestLog(
                    method=request.method,
                    path=request.url.path,
                    ip=request.client.host if request.client else "unknown"
                )
                session.add(log_entry)
                await session.commit()
            except Exception as e:
                await session.rollback()
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Failed to log request",
                        "details": str(e)
                    }
                )

        response = await call_next(request)
        return response
