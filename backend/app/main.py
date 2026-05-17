"""FastAPI application entry point for Meetrix."""
import logging
import sys
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

from app.api.v1.routes import router as v1_router
from app.config import settings
from app.database import initialize_database
from app.graph.analysis_builder import build_analysis_graph
from app.graph.interaction_builder import build_interaction_graph
from app.llm import get_llm

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    setup_logging()
    logger.info("Starting Meetrix backend")

    # Check Ollama connectivity
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(settings.OLLAMA_BASE_URL)
            if r.status_code == 200:
                logger.info("Ollama connected at %s", settings.OLLAMA_BASE_URL)
            else:
                logger.warning(
                    "Ollama responded %d — agents may fail", r.status_code
                )
        except Exception as e:
            logger.warning(
                "Ollama unreachable at %s — start with 'ollama serve': %s",
                settings.OLLAMA_BASE_URL,
                str(e),
            )

    # Warm up default model (prevents cold-start latency on first LLM call).
    # The pipeline's algorithmic nodes (4 of 5) work without Ollama.
    # Only extract_node and synthesize_node require Ollama; they degrade gracefully.
    try:
        llm = get_llm(model_name=settings.ACTION_ITEM_MODEL, temperature=0.0)
        await llm.ainvoke([HumanMessage(content="ping")])
        logger.info("Model pre-loaded: %s", settings.ACTION_ITEM_MODEL)
    except Exception as e:
        logger.warning(
            "Model warm-up failed — LLM nodes will degrade gracefully, "
            "algorithmic analysis still runs: %s",
            e,
        )

    # Initialize database schema
    try:
        await initialize_database()
        logger.info("Database initialized at %s", settings.DATABASE_PATH)
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        raise

    # Build and store compiled graphs
    try:
        app.state.analysis_graph = build_analysis_graph()
        logger.info("Analysis graph compiled (5 nodes, 2 LLM calls)")
    except Exception as e:
        logger.error("Analysis graph compilation failed: %s", e)
        raise

    try:
        app.state.interaction_graph = build_interaction_graph()
        logger.info("Interaction graph compiled (3 agents)")
    except Exception as e:
        logger.error("Interaction graph compilation failed: %s", e)
        raise

    logger.info("Meetrix backend ready")

    yield

    logger.info("Shutting down Meetrix backend")


app = FastAPI(
    title="Meetrix API",
    version="1.0.0",
    description="Meeting intelligence platform — analyze calendar data, detect waste, generate insights",
    lifespan=lifespan,
)

# CORS middleware — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(v1_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def generic_error_handler(request, exc: Exception):
    """Catch-all error handler — log and return 500."""
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Check server logs."},
    )

# Made with Bob
