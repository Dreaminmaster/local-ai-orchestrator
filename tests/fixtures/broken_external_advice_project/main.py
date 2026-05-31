import sys


def buggy_function():
    msg = UNDEFINED_VARIABLE
    print(msg)


if __name__ == "__main__":
    buggy_function()
