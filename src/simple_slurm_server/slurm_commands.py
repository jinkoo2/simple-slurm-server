import subprocess
import json

def run_command(command):
    """Run a shell command with 'module load slurm'."""
    try:
        full_command = f"module load slurm && {command}"
        #print(f'full_command={full_command}')
        result = subprocess.run(
            ["bash", "-c", full_command], stdout=subprocess.PIPE, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise
    
def get_jobs():
    command = "squeue"
    result = run_command(command)
    return parse_squeue_results(result)   
    
def parse_squeue_results(result):
    # Split the output into lines
    lines = result.strip().split('\n')
    
    # Extract headers from the first line and strip whitespace
    headers = lines[0].lower().split()[:6]
    
    # Initialize list to store dictionaries
    jobs = []
    
    # Process each data row (skip the header line)
    for line in lines[1:]:
        # Split the line into columns (assuming space-separated)
        columns = line.split()[:6]
        
        # Create a dictionary for this job
        job_dict = dict(zip(headers, columns))
        jobs.append(job_dict)
    
    return jobs

def get_jobs_of_user(user_id):
    command = "squeue -u "+user_id
    result = run_command(command)
    return parse_squeue_results(result)   

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
        
    def test_jobs_of_uesr():
        user_id = 'jinkokim'
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
    test_jobs_of_uesr()

