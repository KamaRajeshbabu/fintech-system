from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import transactions, auth
from app.core.database import Base, engine
from decimal import Decimal
import logging
import json
import os

logger = logging.getLogger(__name__)

# Custom JSONResponse that handles Decimal values
class DecimalJSONResponse(JSONResponse):
    def render(self, content):
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=lambda o: float(o) if isinstance(o, Decimal) else o.__dict__ if hasattr(o, '__dict__') else str(o)
        ).encode("utf-8")

# Try to create tables, but don't fail if database is not available yet
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables on startup: {e}")
    logger.info("Tables will be created when database becomes available")

app = FastAPI(
    title="Fintech Backend System",
    description="Production-grade financial transaction system with snapshot-based balance engine",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to call backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(transactions.router, prefix="/api/transactions")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    return DecimalJSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.get("/")
def root():
    """Serve the frontend dashboard"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    return {
        "service": "Fintech Backend",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/api/auth/register, /api/auth/login",
            "transactions": "/api/transactions/",
            "frontend": "/"
        }
    }
