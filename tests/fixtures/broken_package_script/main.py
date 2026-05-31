import subprocess
import sys


def main():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from subprocess import run; run(['nonexistent-bin'])",
        ],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout or "")
    sys.stderr.write(result.stderr or "")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
