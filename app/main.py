from fastapi import FastAPI

from app.config import get_settings
from app.controllers.routing import router as routing_router
from app.services.solvers import auto_register_all

settings = get_settings()
auto_register_all()

app = FastAPI(
    title=settings.APP_PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Lexicon-guided route refinement: customer messages -> temporal preferences -> refined delivery route.",
    swagger_ui_parameters={"operationsSorter": "alpha", "tagsSorter": "alpha"},
)
app.include_router(routing_router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": settings.APP_PROJECT_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
