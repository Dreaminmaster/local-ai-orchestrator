def main():
    import sys

    sys.stdout.write("broken import\n")
    import nonexistent_module  # ruff: noqa: F401, F821


if __name__ == "__main__":
    main()
