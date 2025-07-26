from fastapi import FastAPI, Request
from runner import run_and_log
import os
from pathlib import Path

# === Project Definition Classes ===
class Command:
    def __init__(self, cmd: list[str], cwd: str):
        self.cmd = cmd
        self.cwd = cwd

class Project:
    def __init__(self, directory: str, repository: str, commands: list[Command]):
        self.directory = directory
        self.repository = repository
        self.commands = commands

# === Project Configuration ===
PROJECT_PATHS = {
    "novelty_checker_frontend": "/root/novelty_checker_frontend",
}

PROJECTS = {
    "novelty_checker_frontend": Project(
        PROJECT_PATHS["novelty_checker_frontend"],
        "https://thathammadali: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@github.com/MuhammadAnas1657/novelty_checker_frontend",
        [
            Command(["npm", "install"], PROJECT_PATHS["novelty_checker_frontend"]),
            Command(["npm", "run", "build"], PROJECT_PATHS["novelty_checker_frontend"]),
            Command(["npm", "run", "start"], PROJECT_PATHS["novelty_checker_frontend"]),
        ],
    )
}

# === App Init ===
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "awaiting projects..."}

@app.post("/update")
async def update(request: Request):
    try:
        payload = await request.json()
        repo_full_name = payload["repository"]["full_name"]
        repo_name = repo_full_name.split("/")[-1]

        # Log request for debug
        with open("/root/test.log", "a") as test:
            test.write(f"\nPayload: {payload}\nRepo Name: {repo_name}\n")

        if repo_name not in PROJECTS:
            return {"error": f"Unknown repo: {repo_name}"}

        project = PROJECTS[repo_name]
        project_dir = Path(project.directory)

        # Clone or Pull
        if not project_dir.exists():
            run_and_log(
                ["git", "clone", project.repository, str(project_dir)],
                project_dir.parent
            )
        else:
            run_and_log(["git", "pull"], str(project_dir))

        # Run associated commands
        for cmd in project.commands:
            run_and_log(cmd.cmd, cmd.cwd)

        return {"status": f"{repo_name} updated successfully"}

    except Exception as e:
        # Log any exception
        with open("/root/test.log", "a") as test:
            test.write(f"\n[ERROR] {str(e)}\n")
        return {"error": str(e)}
