def main():
    try:
        import pandas_xyz_not_a_real_package  # ruff: noqa: F401
    except ImportError as exc:
        print(f"ImportError: {exc}")
        raise


if __name__ == "__main__":
    main()
