import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Annotated, cast

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from rasheed.api.schemas import (
    DecisionData,
    ErrorData,
    ErrorResponse,
    HealthData,
    HealthResponse,
    PredictionResponse,
    PredictRequest,
    StatisticsResponse,
)
from rasheed.service.interfaces import StoreUnavailable
from rasheed.service.screening import ScreeningService

logger = logging.getLogger("rasheed")
ServiceFactory = Callable[[], ScreeningService]


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorData(code=code, message=message), trace_id=request.state.trace_id
    )
    return JSONResponse(status_code=status, content=body.model_dump())


def get_service(request: Request) -> ScreeningService:
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise StoreUnavailable("Startup is incomplete")
    return cast(ScreeningService, service)


ServiceDependency = Annotated[ScreeningService, Depends(get_service)]


def create_app(factory: ServiceFactory) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        service = await run_in_threadpool(factory)
        try:
            await run_in_threadpool(service.warm_up)
            if not await run_in_threadpool(service.ready):
                raise RuntimeError("Supporting service is not ready")
            app.state.service = service
            logger.info("service_ready")
            yield
        finally:
            app.state.service = None
            await run_in_threadpool(service.close)
            logger.info("service_stopped")

    app = FastAPI(title="Rasheed | Scholarship screening", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def trace_and_log(request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("X-Trace-Id", "")
        # Always generate an opaque ID; arbitrary user text never becomes a log field.
        trace_id = supplied if re.fullmatch(r"[a-f0-9]{32}", supplied) else uuid.uuid4().hex
        request.state.trace_id = trace_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            response = error_response(
                request,
                500,
                "INTERNAL_ERROR",
                "Unexpected error. Contact support with the trace ID.",
            )
        response.headers["X-Trace-Id"] = trace_id
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        response.headers["X-Response-Time-Ms"] = str(elapsed)
        logger.info(
            "request_completed",
            extra={
                "trace_id": trace_id,
                "status_code": response.status_code,
                "duration_ms": elapsed,
            },
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            request,
            422,
            "INVALID_REQUEST",
            "Body must match the documented field types and ranges.",
        )

    @app.exception_handler(StoreUnavailable)
    async def unavailable(request: Request, exc: StoreUnavailable) -> JSONResponse:
        return error_response(request, 503, "NOT_READY", "Service is temporarily unavailable.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error_response(request, exc.status_code, "HTTP_ERROR", "Request cannot be served.")

    @app.get("/health", response_model=HealthResponse, include_in_schema=False)
    @app.get("/v1/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        return HealthResponse(data=HealthData(status="ok"), trace_id=request.state.trace_id)

    @app.get("/ready", response_model=HealthResponse, include_in_schema=False)
    @app.get("/v1/ready", response_model=HealthResponse)
    def ready(request: Request, service: ServiceDependency) -> HealthResponse:
        if not service.ready():
            raise StoreUnavailable()
        return HealthResponse(data=HealthData(status="ready"), trace_id=request.state.trace_id)

    @app.post(
        "/v1/predict",
        response_model=PredictionResponse,
        responses={
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    def predict(
        body: PredictRequest, request: Request, service: ServiceDependency
    ) -> PredictionResponse:
        outcome = service.predict(body.to_domain())
        return PredictionResponse(
            data=DecisionData.model_validate(asdict(outcome)), trace_id=request.state.trace_id
        )

    @app.get("/v1/statistics", response_model=StatisticsResponse)
    def statistics(request: Request, service: ServiceDependency) -> StatisticsResponse:
        return StatisticsResponse(
            data=service.statistics.snapshot(), trace_id=request.state.trace_id
        )

    return app
