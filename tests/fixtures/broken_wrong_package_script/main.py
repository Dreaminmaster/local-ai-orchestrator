import subprocess
import sys


def main():
    result = subprocess.run(["nonexistent_tool_bin", "--version"], capture_output=True, text=True)
    print(result.stdout or "")
    print(result.stderr or "", file=sys.stderr)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
