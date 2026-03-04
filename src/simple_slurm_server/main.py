import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Load environment (including SLURM_USER_ID_LIST) before importing routers
load_dotenv()

from simple_slurm_server.api.v1.jobs import router as jobs_router

app = FastAPI(
    title="Simple Slurm Server",
    description="REST API for querying and controlling SLURM jobs (list, details, cancel, suspend, resume).",
    version="0.1.0",
    openapi_tags=[
        {"name": "Jobs", "description": "SLURM job listing, details, and lifecycle actions."},
    ],
)
app.include_router(jobs_router, prefix="/api/v1", tags=["Jobs"])

# Dashboard at root: redirect / to dashboard; static files under /dashboard
_dashboard_dir = Path(__file__).resolve().parent / "dashboard"
if _dashboard_dir.is_dir():
    @app.get("/", include_in_schema=False)
    def _root():
        return RedirectResponse(url="/dashboard/", status_code=302)
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")



def main():
    """Run the server (entry point for `poetry run main`)."""
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7788"))
    uvicorn.run(
        "simple_slurm_server.main:app",
        host=host,
        port=port,
        reload=True,
    )

