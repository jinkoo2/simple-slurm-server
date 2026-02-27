from typing import Any, Dict, List, Optional
import os

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from ... import slurm_commands as sl

router = APIRouter()

JOB_STATE_SUSPENDED = "SUSPENDED"
JOB_STATE_RUNNING = "RUNNING"


# ----- Request/Response models (OpenAPI schema) -----

class JobStateUpdate(BaseModel):
    """Request body for updating a job's state (suspend or resume)."""
    state: str = Field(
        ...,
        description="New job state. Use `SUSPENDED` to suspend or `RUNNING` to resume.",
        examples=["SUSPENDED", "RUNNING"],
    )


class MessageResponse(BaseModel):
    """Generic success message returned by action endpoints."""
    message: str = Field(..., description="Human-readable result message.")


# ----- Endpoints -----

@router.get(
    "/jobs",
    response_model=List[Dict[str, Any]],
    summary="List jobs",
    description="Return all SLURM jobs in the queue. Optionally filter by user with the `user` query parameter.",
    responses={
        200: {"description": "List of job summaries (e.g. jobid, name, user, st, time)."},
        500: {"description": "SLURM or server error."},
    },
)
async def list_jobs(
    user: Optional[str] = Query(None, alias="user", description="Filter jobs by this user ID."),
):
    try:
        if user:
            return sl.get_jobs_of_user(user)
        return sl.get_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/jobs/{job_id}",
    response_model=Dict[str, Any],
    summary="Get job details",
    description="Return full details of a single SLURM job (from `scontrol show job`).",
    responses={
        200: {"description": "Job details (key-value pairs from SLURM)."},
        500: {"description": "SLURM or server error (e.g. invalid job_id)."},
    },
)
async def get_job(
    job_id: str = Path(..., description="SLURM job ID."),
):
    try:
        return sl.get_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _read_job_file_by_field(job_id: str, field: str) -> str:
    """
    Helper to read a job-related file (e.g. Command, StdOut, StdErr) from the
    details returned by `scontrol show job`.
    """
    try:
        job = sl.get_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    path = job.get(field)
    if not path:
        raise HTTPException(
            status_code=404,
            detail=f"{field} path not available for job {job_id}",
        )

    if not os.path.isfile(path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found for {field}: {path}",
        )

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read {field} file: {e}",
        )


@router.get(
    "/jobs/{job_id}/command",
    response_class=PlainTextResponse,
    summary="Get job Command file contents",
    description="Return the contents of the job's Command file (typically the Slurm script).",
)
async def get_job_command(
    job_id: str = Path(..., description="SLURM job ID."),
):
    return _read_job_file_by_field(job_id, "Command")


@router.get(
    "/jobs/{job_id}/stdout",
    response_class=PlainTextResponse,
    summary="Get job StdOut file contents",
    description="Return the contents of the job's StdOut file.",
)
async def get_job_stdout(
    job_id: str = Path(..., description="SLURM job ID."),
):
    return _read_job_file_by_field(job_id, "StdOut")


@router.get(
    "/jobs/{job_id}/stderr",
    response_class=PlainTextResponse,
    summary="Get job StdErr file contents",
    description="Return the contents of the job's StdErr file.",
)
async def get_job_stderr(
    job_id: str = Path(..., description="SLURM job ID."),
):
    return _read_job_file_by_field(job_id, "StdErr")


@router.delete(
    "/jobs/{job_id}",
    response_model=MessageResponse,
    summary="Cancel job",
    description="Cancel (remove) a SLURM job from the queue. Equivalent to `scancel`.",
    responses={
        200: {"description": "Job canceled successfully."},
        500: {"description": "SLURM or server error."},
    },
)
async def cancel_job(
    job_id: str = Path(..., description="SLURM job ID to cancel."),
):
    try:
        sl.cancel_job(job_id)
        return MessageResponse(message=f"Job {job_id} has been canceled.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/jobs/{job_id}",
    response_model=MessageResponse,
    summary="Update job state",
    description="Suspend or resume a SLURM job. Send `{\"state\": \"SUSPENDED\"}` to suspend or `{\"state\": \"RUNNING\"}` to resume.",
    responses={
        200: {"description": "Job state updated successfully."},
        400: {"description": "Invalid or unsupported state value."},
        500: {"description": "SLURM or server error."},
    },
)
async def update_job_state(
    job_id: str = Path(..., description="SLURM job ID to update."),
    body: JobStateUpdate = ...,
):
    try:
        s = (body.state or "").upper()
        if s == JOB_STATE_SUSPENDED:
            sl.suspend_job(job_id)
            return MessageResponse(message=f"Job {job_id} has been suspended.")
        if s == JOB_STATE_RUNNING:
            sl.resume_job(job_id)
            return MessageResponse(message=f"Job {job_id} has been resumed.")
        raise HTTPException(status_code=400, detail='Invalid state. Use "SUSPENDED" or "RUNNING".')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
