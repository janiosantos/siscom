import os
import requests

GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
RUN_ID = os.getenv("GITHUB_RUN_ID")
API_BASE = "https://api.github.com"

def get_failed_job_id():
    url = f"{API_BASE}/repos/{REPO}/actions/runs/{RUN_ID}/jobs"
    res = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    jobs = res.json().get("jobs", [])

    for job in jobs:
        if job["conclusion"] == "failure":
            print(f"Found failing job: {job['name']}")
            return job["id"]

    print("No failing job found.")
    return None

def download_logs(job_id):
    url = f"{API_BASE}/repos/{REPO}/actions/jobs/{job_id}/logs"
    res = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})

    if res.status_code != 200:
        print(f"Could not download logs for job {job_id}")
        print(res.text)
        return

    with open(f"logs/job_{job_id}.log", "wb") as f:
        f.write(res.content)

    print(f"Saved logs to logs/job_{job_id}.log")

if __name__ == "__main__":
    job_id = get_failed_job_id()
    if job_id:
        download_logs(job_id)
