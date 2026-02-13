# AGENTS.md – simple-slurm-server

Guidance for AI agents working on the simple-slurm-server project.

---

## Project overview

**simple-slurm-server** is a FastAPI server that runs Slurm commands (`squeue`, `scontrol`, `scancel`, etc.) and exposes the results as a REST API. It includes a built-in static dashboard (HTML/JS) served at `/dashboard/`. The server is designed for HPC environments where Slurm is loaded via `module load slurm`; it runs those commands in a subprocess.

- **Consumers**: e.g. **nnunet_job_scheduler** uses `simple_slurm_server.slurm_commands` as a library (Python import). The HTTP API is used by the built-in dashboard or other clients.
- **Config**: Optional `.env` for `HOST` and `PORT` (defaults: 0.0.0.0, 7788).

---

## Repository layout

```
simple-slurm-server/
├── AGENTS.md
├── .env
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── requirements.txt
├── README.md
├── start_server.sh
├── test.py
└── src/simple_slurm_server/
    ├── main.py              # FastAPI app, mounts API and dashboard
    ├── slurm_commands.py    # run_command(), get_jobs(), get_job(), cancel_job(), etc.
    ├── api/v1/jobs.py       # REST routes: GET/DELETE/PATCH /api/v1/jobs, /api/v1/jobs/{id}
    └── dashboard/
        └── index.html       # Built-in dashboard (table + detail panel, filter, sort)
```

---

## Server (simple_slurm_server)

### How it runs Slurm

- Every Slurm call goes through **`run_command(command)`** in `slurm_commands.py`, which runs:
  - `module load slurm && <command>`
- The server process must run in an environment where `module` is available.

### API (prefix `/api/v1`)

| Method   | Path           | Description |
|----------|----------------|-------------|
| GET      | `/api/v1/jobs` | List jobs; optional `?user=<user_id>` |
| GET      | `/api/v1/jobs/{job_id}` | Job details (`scontrol show job`) |
| DELETE   | `/api/v1/jobs/{job_id}` | Cancel job |
| PATCH    | `/api/v1/jobs/{job_id}` | Update state; body `{"state": "SUSPENDED"}` or `"RUNNING"` |

All endpoints return JSON. OpenAPI docs at `/docs`, ReDoc at `/redoc`.

### slurm_commands.py – main symbols

- **run_command(command)** – Runs `module load slurm && <command>`; returns stdout; raises on non-zero exit.
- **get_jobs()**, **get_jobs_of_user(user_id)** – Run `squeue`, return list of dicts (first 6 columns).
- **get_job(job_id)** – `scontrol show job` → flat key-value dict.
- **cancel_job(job_id)**, **suspend_job(job_id)**, **resume_job(job_id)** – `scancel` / `scontrol suspend` / `scontrol resume`.

### Running the server

- From project root: `./start_server.sh` or `poetry run main`. **start_server.sh** loads Python module, creates/activates `_venv`, installs deps, runs `poetry run main`.
- Server listens on **HOST**/ **PORT** from `.env` (default 0.0.0.0:7788).
- Root `/` redirects to `/dashboard/`; dashboard is served from `src/simple_slurm_server/dashboard/`.

### Using as a library

- Install from git: `simple-slurm-server @ git+https://github.com/jinkoo2/simple-slurm-server.git@main` (or equivalent).
- Usage: `from simple_slurm_server import slurm_commands` then e.g. `slurm_commands.get_jobs_of_user(user_id)`.

---

## Conventions and tips for agents

- **.env**: Optional; used for HOST and PORT. Don’t require other config unless the user asks.
- **Errors**: Slurm failures propagate as 500 with `detail` string. Keep unless structured codes are requested.
- **Parsing**: `parse_squeue_results` in slurm_commands assumes default `squeue` and 6 columns; document or extend if changing.
- **Dashboard**: Static files in `src/simple_slurm_server/dashboard/`; API base is `/api/v1`. Update dashboard JS if routes change.

---

## Summary for agents

- **simple-slurm-server** = single project root (no `server/` subfolder). FastAPI app in `src/simple_slurm_server/`; API under `/api/v1`, built-in dashboard at `/dashboard/`, default port 7788.
- **Library use**: Other projects import `simple_slurm_server.slurm_commands` and call `get_jobs()`, `get_jobs_of_user()`, etc.

# Change history
- added a simple dashboard to this server root, and removed dashboard-react project