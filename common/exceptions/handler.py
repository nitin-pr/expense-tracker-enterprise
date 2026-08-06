import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .base import AppException

logger = logging.getLogger(__name__)


def app_exception_handler(exc, context):
    """Custom exception handler for DRF that handles AppException and its subclasses."""
    if isinstance(exc, AppException):
        logger.error("%s: %s", exc.code, exc.message, extra={"details": exc.details})
        return Response(
            {"code": exc.code, "message": exc.message, "details": exc.details},
            status=exc.http_status,
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    logger.error("Unhandled exception", exc_info=exc)
    return Response(
        {"code": "server_error", "message": "An unexpected error occurred.", "details": {}},
        status=500,
    )
