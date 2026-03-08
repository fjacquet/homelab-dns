"""Ansible Webhook Engine — FastAPI service for triggering Ansible playbooks via HTTP."""

import json
import os
import secrets
import subprocess
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PLAYBOOKS_DIR = Path(os.getenv("PLAYBOOKS_DIR", "/playbooks"))
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")
LOG_TAIL = int(os.getenv("LOG_TAIL", "100"))

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(key: str = Security(api_key_header)) -> str:
    if not WEBHOOK_API_KEY:
        raise RuntimeError("WEBHOOK_API_KEY environment variable is not set")
    if not secrets.compare_digest(key, WEBHOOK_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    accepted = "accepted"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class RunRequest(BaseModel):
    playbook: str
    tags: str | None = None
    limit: str | None = None
    extra_vars: dict[str, Any] | None = None

    @field_validator("playbook")
    @classmethod
    def playbook_safe(cls, v: str) -> str:
        """Reject path traversal and non-YAML filenames."""
        if "/" in v or ".." in v:
            raise ValueError("playbook must be a filename, not a path")
        if not v.endswith((".yml", ".yaml")):
            raise ValueError("playbook must be a .yml or .yaml file")
        return v


class JobState(BaseModel):
    job_id: str
    playbook: str
    status: JobStatus
    created_at: str
    finished_at: str | None = None
    returncode: int | None = None
    log_lines: list[str] = []


# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------

jobs: dict[str, JobState] = {}

# ---------------------------------------------------------------------------
# Background runner
# ---------------------------------------------------------------------------


def _run_playbook(job_id: str, request: RunRequest) -> None:
    """Execute ansible-playbook in a background thread and stream output to the job log."""
    job = jobs[job_id]
    job.status = JobStatus.running

    playbook_path = PLAYBOOKS_DIR / request.playbook
    inventory_path = PLAYBOOKS_DIR / "inventory.yml"

    cmd = [
        "ansible-playbook",
        "-i", str(inventory_path),
        str(playbook_path),
    ]
    if request.tags:
        cmd += ["--tags", request.tags]
    if request.limit:
        cmd += ["--limit", request.limit]
    if request.extra_vars:
        cmd += ["--extra-vars", json.dumps(request.extra_vars)]

    job.log_lines.append(
        f"[{datetime.now(timezone.utc).isoformat()}] Running: {' '.join(cmd)}"
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            job.log_lines.append(line.rstrip())
        proc.wait()
        job.returncode = proc.returncode
        job.status = (
            JobStatus.succeeded if proc.returncode == 0 else JobStatus.failed
        )
    except Exception as exc:  # noqa: BLE001
        job.log_lines.append(f"ERROR launching playbook: {exc}")
        job.status = JobStatus.failed

    job.finished_at = datetime.now(timezone.utc).isoformat()
    job.log_lines.append(
        f"[{job.finished_at}] Job {job_id} finished with status {job.status}"
    )


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ansible Webhook Engine",
    description=(
        "Trigger Ansible playbooks via HTTP POST from n8n or any webhook caller.\n\n"
        "## Authentication\n"
        "All endpoints except `/health` require an `X-API-Key` header.\n"
        "Click **Authorize** above and enter your API key.\n\n"
        "## Usage\n"
        "1. `GET /playbooks` — list available playbooks\n"
        "2. `POST /run` — submit a job, receive a `job_id`\n"
        "3. `GET /status/{job_id}` — poll until `status` is `succeeded` or `failed`"
    ),
    version="1.0.0",
    contact={"name": "homelab-dns", "url": "https://github.com/fjacquet/homelab-dns"},
    license_info={"name": "MIT"},
)


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness probe — no authentication required."""
    return {
        "status": "ok",
        "playbooks_dir": str(PLAYBOOKS_DIR),
        "playbooks_dir_mounted": PLAYBOOKS_DIR.exists(),
    }


@app.get("/playbooks", tags=["ops"])
def list_playbooks(_api_key: str = Depends(verify_api_key)) -> dict:
    """List available playbooks in the mounted playbooks directory."""
    if not PLAYBOOKS_DIR.exists():
        raise HTTPException(status_code=503, detail="Playbooks directory is not mounted")
    playbooks = sorted(p.name for p in PLAYBOOKS_DIR.glob("*.yml") if p.is_file())
    return {"playbooks": playbooks, "playbooks_dir": str(PLAYBOOKS_DIR)}


@app.post("/run", status_code=202, tags=["jobs"])
def run(
    request: RunRequest,
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Accept a playbook run request and execute it asynchronously.

    Returns HTTP 202 immediately with a `job_id`. Poll `/status/{job_id}` for results.
    """
    playbook_path = PLAYBOOKS_DIR / request.playbook
    if not playbook_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Playbook '{request.playbook}' not found in {PLAYBOOKS_DIR}",
        )

    job_id = str(uuid.uuid4())
    jobs[job_id] = JobState(
        job_id=job_id,
        playbook=request.playbook,
        status=JobStatus.accepted,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    thread = Thread(target=_run_playbook, args=(job_id, request), daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "accepted"}


@app.get("/status/{job_id}", tags=["jobs"])
def status(
    job_id: str,
    tail: int = LOG_TAIL,
    _api_key: str = Depends(verify_api_key),
) -> JobState:
    """Return job status and the last `tail` lines of output (default: 100)."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    result = job.model_copy()
    result.log_lines = job.log_lines[-tail:]
    return result
