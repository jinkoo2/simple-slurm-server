# simple-slurm-server

Minimal FastAPI service that exposes a REST API around basic Slurm job operations (list, inspect, cancel, suspend, resume). It is intended to be a small, self-contained helper service that other tools can call instead of shelling out to `squeue`, `scontrol`, and `scancel` directly.

## Features

- **Job listing**: wrap `squeue` to list all jobs or only jobs for a given user.
- **Job details**: wrap `scontrol show job <jobid>` and return key–value pairs.
- **Cancel jobs**: wrap `scancel <jobid>`.
- **Suspend / resume jobs**: wrap `scontrol suspend` / `scontrol resume`.
- **Simple dashboard (optional)**: static HTML dashboard under `/dashboard` if the `dashboard/` directory is present.

## API

The FastAPI app is defined in `src/simple_slurm_server/main.py` and mounts the v1 jobs router under `/api/v1`.

- `GET /api/v1/jobs`
  - List all Slurm jobs. Optional query param `user` filters by Unix user.
- `GET /api/v1/jobs/{job_id}`
  - Return details for a single job (parsed from `scontrol show job`).
- `DELETE /api/v1/jobs/{job_id}`
  - Cancel a job (equivalent to `scancel {job_id}`).
- `PATCH /api/v1/jobs/{job_id}`
  - Update job state by sending a JSON body:
    - `{"state": "SUSPENDED"}` → `scontrol suspend {job_id}`
    - `{"state": "RUNNING"}`   → `scontrol resume {job_id}`

OpenAPI docs are available at `/docs` when the server is running.

## Configuration

Environment variables are loaded via `python-dotenv` (`load_dotenv()` in `main.py`).

| Variable | Description | Default |
|---------|-------------|---------|
| `HOST`  | Host interface to bind the API server to. | `0.0.0.0` |
| `PORT`  | TCP port for the API server. | `7788` |

The service assumes that:

- Slurm CLI tools (`squeue`, `scontrol`, `scancel`) are available in the environment.
- The command `module load slurm` works and exposes these tools. Every Slurm call is executed as `module load slurm && <command>` in `slurm_commands.run_command`.

## Quick Start

### Local (without Docker)

```bash
cd simple-slurm-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export HOST=0.0.0.0
export PORT=7788
uvicorn simple_slurm_server.main:app --host "$HOST" --port "$PORT" --reload
```

Then open:

- `http://localhost:7788/docs` for API docs.
- `http://localhost:7788/dashboard/` if the dashboard folder is present.

### With Poetry (if you use pyproject.toml)

```bash
poetry install
poetry run python -m simple_slurm_server.main
```

## Project Layout

- `src/simple_slurm_server/main.py` — FastAPI app and entry point.
- `src/simple_slurm_server/api/v1/jobs.py` — `/api/v1/jobs` endpoints and request/response models.
- `src/simple_slurm_server/slurm_commands.py` — thin wrappers around Slurm CLI (`squeue`, `scontrol`, `scancel`) with JSON-friendly output.
- `src/simple_slurm_server/dashboard/` — optional static dashboard (if present, served under `/dashboard`).
- `requirements.txt` — runtime + dev dependencies.

## Notes

- All Slurm interactions go through `slurm_commands.py`. If you need new capabilities (e.g. filtering by partition), extend that module and keep the `run_command("module load slurm && ...")` pattern.
- The API is intentionally minimal; higher-level orchestration (job scheduling, policies, tracking) should live in a separate service. 
