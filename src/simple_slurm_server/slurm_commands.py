import subprocess
import json
from typing import List, Dict, Optional


def run_command(command: str) -> str:
    """Run a shell command with 'module load slurm'."""
    try:
        full_command = f"module load slurm && {command}"
        result = subprocess.run(
            ["bash", "-c", full_command],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise


# sacct fields:
#   JobID | JobName | Partition | State | Start | End | Elapsed | MaxRSS | ReqMem
SACCT_FORMAT = "JobID,JobName%60,Partition,State,Start,End,Elapsed,MaxRSS,ReqMem"
SACCT_FIELDS = ["jobid", "name", "partition", "state", "start", "end", "time", "maxrss", "reqmem"]


def parse_sacct_results(result: str, user: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Parse sacct output (without header, parsable/pipe-delimited) into a list of dicts.
    """
    if not result:
        return []

    jobs: List[Dict[str, str]] = []
    for line in result.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != len(SACCT_FIELDS):
            continue
        job = dict(zip(SACCT_FIELDS, parts))
        # Normalize to the shape expected by the dashboard:
        # - user: we know it from the sacct -u argument
        # - st: short/primary state string
        # - start / end: timestamps
        # - time: elapsed
        # - nodelist: reuse partition column (we don't have nodes here)
        job_dict: Dict[str, str] = {
            "jobid": job["jobid"],
            "name": job["name"],
            "user": user or "",
            "partition": job["partition"],
            "state": job["state"],
            "st": job["state"],
            "start": job["start"],
            "end": job["end"],
            "time": job["time"],
            "maxrss": job["maxrss"],
            "reqmem": job["reqmem"],
            "nodelist": job["partition"],
        }
        jobs.append(job_dict)

    return jobs


def get_jobs(user: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get jobs from sacct. If user is provided, limit to that user; otherwise
    query all users (not used by the dashboard in practice). Use -S 1970-01-01
    so we see the full history (past, present, future-reserved).
    """
    base_cmd = "sacct -P -n -S 1970-01-01 --format={fmt}".format(fmt=SACCT_FORMAT)
    if user:
        base_cmd = f"sacct -u {user} -P -n -S 1970-01-01 --format={SACCT_FORMAT}"
    result = run_command(base_cmd)
    return parse_sacct_results(result, user=user)


def get_jobs_of_user(user_id: str) -> List[Dict[str, str]]:
    """
    Get all (past + present) jobs for a specific user via sacct.
    """
    command = f"sacct -u {user_id} -P -n -S 1970-01-01 --format={SACCT_FORMAT}"
    result = run_command(command)
    return parse_sacct_results(result, user=user_id)

def get_job_from_job_name(job_name, user_id=None):

    if user_id is None:
        jobs = get_jobs()
    else:
        jobs = get_jobs_of_user(user_id)
    
    jobs_found = [job for job in jobs if job['name'] == job_name]

    if len(jobs_found) == 0:
        return None
    elif len(jobs_found) == 1:
        return jobs_found[0]
    else:
        raise Exception(f"More than 1 job found with job_name={job_name}. jobs_found={jobs_found}")
    

def get_job(job_id):
        command = "scontrol show job " + job_id
        output = run_command(command)

        # Parse output
        job_details = {}
        for line in output.split("\n"):
            for item in line.split():
                if "=" in item:
                    key, value = item.split("=", 1)
                    job_details[key] = value

        
        return job_details


def cancel_job(job_id: str):
    command = f"scancel {job_id}"
    run_command(command)


def suspend_job(job_id: str):
    command = f"scontrol suspend {job_id}"
    run_command(command)

def resume_job(job_id: str):
    command = f"scontrol resume {job_id}"
    run_command(command)

if __name__ == '__main__':
    def test_all_jobs():
        # job list
        print('=== jobs ====')
        jobs = get_jobs()
        print(f'Found {len(jobs)} jobs')
        
        if len(jobs) > 0:
            # job[0]
            print('=== jobs ====')
            print(json.dumps(jobs, indent=4))
            
            # job detail
            print('=== first job detail ====')
            print(json.dumps(get_job(jobs[0]['jobid']), indent=4))
        
    def test_jobs_of_user(user_id: str):
        # job list
        print(f'=== jobs of user[{user_id}] ====')

        jobs = get_jobs_of_user(user_id)
        print(f'Found {len(jobs)} jobs')
        
        if len(jobs) > 0:
            # job[0]
            print('=== first job ====')
            print(json.dumps(jobs[0], indent=4))
            
            # job detail
            print('=== first job detail ====')
            print(json.dumps(get_job(jobs[0]['jobid']), indent=4))


    test_all_jobs()

