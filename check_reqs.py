import subprocess
import sys

try:
    output = subprocess.check_output(
        ["venv\\Scripts\\pip", "install", "-r", "backend\\requirements.txt"],
        stderr=subprocess.STDOUT
    )
    with open("pip_err.txt", "wb") as f:
        f.write(output)
    print("Success")
except subprocess.CalledProcessError as e:
    with open("pip_err.txt", "wb") as f:
        f.write(e.output)
    print("Failed - see pip_err.txt")
