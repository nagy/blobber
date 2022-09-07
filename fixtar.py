#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from subprocess import run
from typing import List
import shutil


# some idempotency comments:
# https://stackoverflow.com/questions/32997526/how-to-create-a-tar-file-that-omits-timestamps-for-its-contents
def make_fixtar(path: Path, tarpath: Path):
    run(
        [
            "tar",
            "--sort=name",
            "--numeric-owner",
            "--owner=0",
            "--group=0",
            "--append",
            "-f",
            tarpath.absolute(),
            ".",
        ],
        check=True,
        cwd=path,
    )


def make_sha256sums(path: Path):
    assert not os.path.exists("SHA256SUMS")
    with open("SHA256SUMS", "wb") as shafile:
        run(
            "find . -type f -exec sha256sum {} \\; | sort",
            shell=True,
            check=True,
            stdout=shafile,
            cwd=path,
        )
        os.chmod(shafile.name, 0o444)


def add_sha256sums(tarpath: Path):
    run(
        [
            "tar",
            "--numeric-owner",
            "--owner=0",
            "--group=0",
            "--mtime=UTC 1970-01-01",
            "-cf",
            tarpath,
            "SHA256SUMS",
        ],
        check=True,
    )


def main(args: List[str] = sys.argv):
    cmd = args[1]
    if cmd == "create":
        for path in args[2:]:
            path = Path(path)
            assert not os.path.exists("SHA256SUMS")
            assert path.is_dir()
            make_sha256sums(path)
            path = path
            tarpath = Path(path.name + ".fix.tar")
            add_sha256sums(tarpath)
            os.remove("SHA256SUMS")
            make_fixtar(path, tarpath)
            shutil.copystat(path, tarpath)
            os.chmod(tarpath, 0o444)
            print(tarpath)
    else:
        print("command not found:", cmd, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
