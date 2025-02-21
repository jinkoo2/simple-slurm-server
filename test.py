import requests
import time

BASE_URL = "http://127.0.0.1:7788"  # FastAPI server URL

def get_slurm_jobs():
    print('getting the list of dataset')
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch task status: {response.status_code}, {response.text}")
        return None

if __name__ == "__main__":
    result = get_slurm_jobs()
    if result is None:
        print("Failed to get dataset list.")
    else:
        for item in result:
            print(item)

    
    