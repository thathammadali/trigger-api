from datetime import datetime
import subprocess
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# === Helper function ===
def run_and_log(cmd, cwd=None):
    timestamp = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
    log_prefix = f"{timestamp} {' '.join(cmd)}"

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)

    with open(LOG_DIR / "stdout.log", "a") as out, open(LOG_DIR / "stderr.log", "a") as err, open(LOG_DIR / "status.log", "a") as stat:
        out.write(f"{log_prefix}\n{result.stdout}\n")
        err.write(f"{log_prefix}\n{result.stderr}\n")
        stat.write(f"{log_prefix}\nExit Code: {result.returncode}\n\n")

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

    return result

def log(description):
    timestamp = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")

    with open(LOG_DIR / "custom.log", "a") as log:
        log.write(f"{timestamp} {description}\n")