from subprocess import Popen
from sys import argv

args = " ".join(argv[1:]) or "."


def main():
    Popen(f"isort {args}").wait()
    Popen(f"black {args}").wait()


if __name__ == "__main__":
    main()
