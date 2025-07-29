import sys
from fastapi import FastAPI, Request
from runner import run_and_log, log
from pathlib import Path

# === Project Definition Classes ===
class Command:
    def __init__(self, cmd: list[str], cwd: str | Path = None):
        self.cmd = cmd
        self.cwd = cwd

class Project:
    def __init__(self, directory: str, repository: str, commands: list[Command]):
        self.directory = directory
        self.repository = repository
        self.commands = commands

def deploy_node_project(project_name):
    project_path = PROJECT_PATHS[project_name]

    return [
        Command(["npm", "install"], project_path),
        Command(["npm", "run", "build"], project_path),
        Command(["bash", "-c", f"pm2 delete {project_name} || true"], project_path),
        Command(["pm2", "start", "npm", "--name", project_name, "--", "run", "start"], project_path),
    ]

def generate_fastapi_service(project_name, service_file, description, port, type = "pip"):
    description = description or f"{project_name} FastAPI Service"
    Path("services").mkdir(exist_ok=True)

    service_content = f'''
    [Unit]
    Description={description}
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/root/{project_name}
    ExecStart={f"/root/{project_name}/venv/bin/uvicorn main:app --host 0.0.0.0 --port {port}" if type == "pip" else f"/bin/bash -c 'source /root/anaconda3/etc/profile.d/conda.sh && conda activate {project_name}_env && uvicorn main:app --host 0.0.0.0 --port {port}'"}
    Restart=always
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=multi-user.target
    '''

    with open(f"services/{str(service_file)}", "w") as f:
        f.write(service_content)

def deploy_fastapi_project(project_name, port, description=None):
    # Project Path
    project_path = Path(PROJECT_PATHS[project_name])

    # Service Files Setup
    service_file = f"{project_name}.service"
    service_path = Path(f"/etc/systemd/system/{service_file}")

    # Commands List
    commands = []

    # Environment file paths
    conda_env_file = project_path / "environment.yml"
    pip_env_file = project_path / "requirements.txt"

    if conda_env_file.exists() and pip_env_file.exists():
        log("Multiple requirement files found!")
        return []
    if conda_env_file.exists():
        log("Conda requirement file found!")
        conda_path = "/root/anaconda3/etc/profile.d/conda.sh"

        full_cmd = (
            f"source {conda_path} && "
            f"(conda env list | grep {project_name}_env && "
            f"conda env update --name {project_name}_env --file environment.yml --prune || "
            f"conda env create -f environment.yml) && "
            f"conda activate {project_name}_env"
        )

        commands.append(
            Command(["bash", "-c", full_cmd],
                    str(project_path))
        )
    elif pip_env_file.exists():
        log("Pip requirement file found!")
        venv_path = project_path / "venv"
        if not venv_path.exists():
            commands.append(
                Command([sys.executable, "-m", "venv", "venv"], str(project_path))
            )

        pip_path = venv_path / "bin/pip"
        commands.append(
            Command([str(pip_path), "install", "-r", "requirements.txt"], str(project_path))
        )
    else:
        log("No requirements file found!")
        return []

    if not Path(f"services/{str(service_file)}").exists():
        generate_fastapi_service(project_name, service_file, description, port)

    if not service_path.exists():
        commands.extend([
            Command(["cp", f"services/{str(service_file)}", str(service_path)]),
            Command(["systemctl", "daemon-reload"]),
            Command(["systemctl", "enable", project_name]),
            Command(["systemctl", "start", project_name]),
        ])
    else:
        commands.append(
            Command(["systemctl", "restart", project_name])
        )

    return commands

# === Project Configuration ===
PROJECT_PATHS = {
    "novelty_checker_frontend": "/root/novelty_checker_frontend",
    "novelty_checker_backend": "/root/novelty_checker_backend",
}

PROJECTS = {
    "novelty_checker_frontend": Project(
        PROJECT_PATHS["novelty_checker_frontend"],
        "https://thathammadali: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@github.com/MuhammadAnas1657/novelty_checker_frontend",
        deploy_node_project("novelty_checker_frontend"),
    ),
    "novelty_checker_backend": Project(
        PROJECT_PATHS["novelty_checker_backend"],
        "https://thathammadali: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@github.com/MuhammadAnas1657/novelty_checker_backend",
        deploy_fastapi_project("novelty_checker_backend", port=8002),
    ),
}

def deploy_project(repo_name):
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
    if project.commands == []:
        return {"status": "No requirements file found"}

    for cmd in project.commands:
        run_and_log(cmd.cmd, cmd.cwd)

    return {"status": f"{repo_name} updated successfully"}

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

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

        return deploy_project(repo_name)
    except Exception as e:
        return {"error": str(e)}

@app.get("/redeploy/{repo_name}")
async def redeploy(repo_name):
    try:
        return deploy_project(repo_name)
    except Exception as e:
        return {"error": str(e)}