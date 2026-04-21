from fastapi import FastAPI
from controllers.telegram import router as telegram_router
from middleware.logger import RequestLoggerMiddleware


def setup_routes(app: FastAPI):
    """
    Setup all routes and middleware for the application
    """
    # Add middleware
    app.add_middleware(RequestLoggerMiddleware)

    # Include routers
    app.include_router(telegram_router, prefix="/api", tags=["telegram"])
