import os
import sys
import subprocess
from pathlib import Path

ENV_DIR = Path(".venv")
REQUIREMENTS = "requirements.txt"

def run_command(cmd, shell=False):
    try:
        subprocess.run(cmd, check=True, shell=shell)
    except subprocess.CalledProcessError:
        print(f"Command failed: {' '.join(cmd)}")
        sys.exit(1)

def create_virtualenv():
    if ENV_DIR.exists():
        print("Virtual environment already exists.")
    else:
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", str(ENV_DIR)])

def install_requirements():
    pip_path = ENV_DIR / "Scripts" / "pip.exe" if os.name == "nt" else ENV_DIR / "bin" / "pip"
    print("Installing dependencies...")
    run_command([str(pip_path), "install", "-r", REQUIREMENTS])

def activate_instructions():
    if os.name == "nt":
        activate_cmd = fr"{ENV_DIR}\Scripts\activate"
        start_cmd = "python main.py"
    else:
        activate_cmd = f"source {ENV_DIR}/bin/activate"
        start_cmd = "python3 main.py"

    print("\nSetup complete.")
    print("Now run the following to activate the environment and start the app:\n")
    print(f"   {activate_cmd}")
    print(f"   {start_cmd}\n")

if __name__ == "__main__":
    if not Path(REQUIREMENTS).exists():
        print(f"Missing {REQUIREMENTS}. Please add it and try again.")
        sys.exit(1)

    create_virtualenv()
    install_requirements()
    activate_instructions()
