# AGENTS – simple-slurm-server

Guidance for AI/code agents working on this project.

---

## Project overview

- **Purpose**: Expose a very small, predictable REST API for querying and controlling Slurm jobs.
- **Scope**: This service is intentionally minimal. It:
  - Wraps `squeue` to list jobs (optionally by user).
  - Wraps `scontrol show job` to inspect a job.
  - Wraps `scancel`, `scontrol suspend`, and `scontrol resume` for lifecycle actions.
  - Optionally serves a static dashboard under `/dashboard`.
- **Non‑goals**: No long‑running job orchestration, scheduling policies, or persistence; those should be handled by higher‑level tools that call this API.

---

## Code layout

- `src/simple_slurm_server/main.py`
  - Creates the FastAPI app, loads `.env` with `load_dotenv()`, and includes the v1 jobs router under `/api/v1`.
  - Entry point `main()` is used by CLI/Poetry to start `uvicorn`.
- `src/simple_slurm_server/api/v1/jobs.py`
  - Defines the `/api/v1/jobs` endpoints:
    - `GET /jobs` — list jobs, optional `user` query filter.
    - `GET /jobs/{job_id}` — job details.
    - `DELETE /jobs/{job_id}` — cancel job.
    - `PATCH /jobs/{job_id}` — suspend / resume job via JSON body `{"state": "SUSPENDED"|"RUNNING"}`.
  - Uses `simple_slurm_server.slurm_commands` for actual Slurm interactions.
- `src/simple_slurm_server/slurm_commands.py`
  - Single place where we shell out to Slurm:
    - `run_command()` runs `module load slurm && <command>` through `bash -c`.
    - `get_jobs()` / `get_jobs_of_user()` parse `squeue` output into a list of dicts.
    - `get_job()` parses `scontrol show job` into a `dict`.
    - `cancel_job()`, `suspend_job()`, `resume_job()` wrap the corresponding SLURM commands.
- `src/simple_slurm_server/dashboard/` (optional)
  - Static HTML/JS dashboard. If present, served at `/dashboard` and `/`.

---

## Configuration & environment

- Environment variables are read via `dotenv` in `main.py`:
  - `HOST` (default `0.0.0.0`) — bind address for the API server.
  - `PORT` (default `7788`) — port for the API server.
- External assumptions:
  - The command `module load slurm` must succeed and expose Slurm tools onto `PATH`.
  - `squeue`, `scontrol`, and `scancel` behave like standard Slurm CLI commands.

When adding new configuration:

- Add the variable usage in code (e.g. via `os.getenv` in `main.py` or `slurm_commands.py`).
- Document it in `README.md` under the **Configuration** table.

---

## Conventions and patterns

- **Slurm command execution**:
  - Always go through `slurm_commands.run_command()`.
  - Preserve the `module load slurm && <command>` convention so the service works in module‑based clusters.
  - Prefer returning JSON‑friendly Python types (dicts/lists) from `slurm_commands` and let FastAPI handle serialization.
- **Parsing**:
  - `parse_squeue_results()` assumes the first row is headers and uses the first 6 columns; if you change headers or need more fields, update both the parser and any API documentation/comments that describe the response shape.
- **API design**:
  - Keep the v1 routes simple and orthogonal:
    - Listing endpoints (`GET /jobs`) should not mutate state.
    - Lifecycle endpoints (`DELETE /jobs/{job_id}`, `PATCH /jobs/{job_id}`) should only perform the requested action.
  - Use clear, user‑facing error messages but do not expose internal tracebacks in HTTP responses.

---

## How to extend safely

When adding features, prefer **composability** over complexity:

- New SLURM queries:
  - Implement a helper in `slurm_commands.py` first (e.g. `get_jobs_by_partition(partition)`).
  - Then add a small API wrapper in `api/v1/jobs.py` that calls it and returns the result.
- New filters/fields:
  - Extend the parser (`parse_squeue_results` or `get_job`) to include additional keys.
  - Be mindful of backwards compatibility: avoid silently removing existing keys from responses used by other services.
- New dashboards:
  - Place static assets under `dashboard/`. `main.py` will automatically mount them if the directory exists.

---

## Things to avoid

- Do **not**:
  - Run arbitrary user‑supplied shell commands; all execution must be built from vetted Slurm CLI calls.
  - Change the way `run_command` builds the command (e.g. removing `module load slurm`) unless you also update deployment docs and know the cluster environment supports it.
  - Introduce long‑running background tasks inside this service; it should remain a thin synchronous wrapper around Slurm.
  - Add heavy dependencies (ORMs, job schedulers, etc.) — keep this project lightweight.

---

## Testing notes

- There is a simple `test.py` which currently calls the root URL and prints JSON.
- For more robust tests, add FastAPI tests using `TestClient` under `tests/` and avoid hitting real Slurm where possible (mock `slurm_commands.run_command`).

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

# Change log
- 2/13/2026: added a simple dashboard to this server root, and removed dashboard-react project