from fastapi import FastAPI, Request
from runner import run_and_log
import os
from pathlib import Path

class Command:
    """
    Represents a command

    Args:
        cmd (list): List of command tokens to execute
        cwd (str): Current working directory
    """
    def __init__(self, cmd: list, cwd: str):
        self.cmd = cmd
        self.cwd = cwd

class Project:
    """
    Represents a project that can be set up or managed via directory, repository, and associated commands.

    Args:
        directory (str): The local path where the project is or will be located.
        repository (str): The URL of the remote Git repository.
        commands (list): A list of shell commands to be run within the project directory.
    """
    def __init__(self, directory: str, repository: str, commands: list):
        self.directory = directory
        self.repository = repository
        self.commands = commands

PROJECT_PATHS = {
    "novelty_checker_frontend": "/root/novelty-checker"
}

PROJECTS = {
    "novelty_checker_frontend": Project(PROJECT_PATHS['novelty_checker_frontend'],
            "https://thathammadali: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@github.com/MuhammadAnas1657/novelty_checker_frontend",
            [
                Command(["npm","install"], PROJECT_PATHS['novelty_checker_frontend']),
                Command(["npm","run","build"], PROJECT_PATHS['novelty_checker_frontend'])
            ])
}

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "awaiting projects..."}

@app.post("/update")
async def update(request: Request):
    payload = await request.json()
    repo_full_name = payload["repository"]["full_name"]
    repo_name = repo_full_name.split("/")[-1]

    if repo_name not in PROJECTS:
        return {"error": f"Unknown repo: {repo_name}"}

    project = PROJECTS[repo_name]

    if not os.path.exists(project.directory):
        run_and_log(["git", "clone", project.repository], Path(project.directory).parent)
    else:
        run_and_log(["git", "pull"], project.directory)

    for cmd in project.commands:
        run_and_log(cmd.cmd, cmd.cwd)

    return {"status": f"{repo_name} updated successfully"}