from fastapi import FastAPI, HTTPException

import slurm_commands as sl

app = FastAPI()

@app.get("/jobs")
async def list_jobs():
    """List all SLURM jobs."""
    try:
        return sl.get_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user_jobs/{user_id}")
async def list_jobs_of_user(user_id: str):
    """List all SLURM jobs."""
    try:
        return sl.get_jobs_of_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/details/{job_id}")
async def get_job_details(job_id: str):
    """Get details of a specific SLURM job."""
    try:
        return sl.get_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/job/cancel/{job_id}")
async def cancel_job_endpoint(job_id: str):
    """Cancel a SLURM job."""
    try:
        sl.cancel_job(job_id)
        return {"message": f"Job {job_id} has been canceled."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job/suspend/{job_id}")
async def suspend_job_endpoint(job_id: str):
    """Suspend a running SLURM job."""
    try:
        sl.suspend_job(job_id)
        return {"message": f"Job {job_id} has been suspended."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job/resume/{job_id}")
async def resume_job_endpoint(job_id: str):
    """Resume a suspended SLURM job."""
    try:
        sl.resume_job(job_id)
        return {"message": f"Job {job_id} has been resumed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

