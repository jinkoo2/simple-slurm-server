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
        command = "module load slurm && squeue"
        output = run_command(command)
 
        # Extract headers
        lines = output.split("\n")
        headers = lines[0].lower().split()

        # Extract job details
        job_list = []

        import re
        
        for line in lines[1:]:
            # Use regex to capture jobid (including array job notation like 1583267_[313-324])
            match = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+\((.+)\)", line.strip())
            if match:
                job_data = dict(zip(headers, match.groups()))
                job_list.append(job_data)
        
        return job_list
    

def get_jobs_of_user(user_id):
        command = "module load slurm && squeue -u "+user_id
        output = run_command(command)
 
        # Extract headers
        lines = output.split("\n")
        headers = lines[0].lower().split()

        # Extract job details
        job_list = []

        import re
        
        for line in lines[1:]:
            # Use regex to capture jobid (including array job notation like 1583267_[313-324])
            match = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+\((.+)\)", line.strip())
            if match:
                job_data = dict(zip(headers, match.groups()))
                job_list.append(job_data)
        
        return job_list

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
            print('=== first job ====')
            print(json.dumps(jobs[0], indent=4))
            
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

