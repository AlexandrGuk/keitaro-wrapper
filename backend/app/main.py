import secrets

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import router
from app.config import settings
from app.editor import NotFound
from app.keitaro import KeitaroError
from app.naming import NamingError
from app.shares import ShareError

app = FastAPI(title="Keitaro wrapper", redirect_slashes=False)
app.include_router(router, prefix="/api")

OPEN_PATHS = {"/login", "/api/login", "/api/logout"}

frontend = settings.frontend_dir


class LoginRequired(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in OPEN_PATHS or path.startswith("/static"):
            return await call_next(request)
        if request.session.get("user"):
            return await call_next(request)
        if path.startswith("/api"):
            return JSONResponse({"detail": "Нужно войти"}, status_code=401)
        return RedirectResponse("login", status_code=303)


@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse(frontend / "login.html")


@app.get("/")
def index_page() -> FileResponse:
    return FileResponse(frontend / "index.html")


@app.get("/campaigns")
def campaigns_page() -> FileResponse:
    return FileResponse(frontend / "campaigns.html")


@app.get("/campaign")
def campaign_page() -> FileResponse:
    return FileResponse(frontend / "campaign.html")


@app.exception_handler(NamingError)
@app.exception_handler(ShareError)
def handle_bad_request(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(NotFound)
def handle_not_found(_request: Request, exc: NotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(KeitaroError)
def handle_keitaro(_request: Request, exc: KeitaroError) -> JSONResponse:
    status = exc.status if 400 <= exc.status < 500 else 502
    return JSONResponse(status_code=status, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
def handle_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
    parts = []
    for error in exc.errors():
        loc = ".".join(str(item) for item in error["loc"] if item != "body")
        parts.append(f"{loc}: {error['msg']}" if loc else error["msg"])
    return JSONResponse(status_code=400, content={"detail": "; ".join(parts)})


app.add_middleware(LoginRequired)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or secrets.token_hex(32),
    session_cookie="wrapper_session",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=settings.session_https,
)
app.mount("/static", StaticFiles(directory=frontend), name="static")
