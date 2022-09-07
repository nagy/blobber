import json
import os
import shutil
import sys

import click

from .blobber import (
    blob_find,
    blob_open,
    blob_stat,
    get_blobs,
    get_storages,
)
from .hash import Hash, hashit
from .storage import FileStorage


@click.group()
def main():
    ...


@main.command()
def ls():
    for blob in get_blobs():
        print(blob)


@main.command()
def ls_names():
    for blob in get_blobs():
        print(blob.name)


@main.command()
def ls_hashes():
    for blob in get_blobs():
        print(blob.hash)


@main.command()
def ls_storage():
    for storage in get_storages():
        print(storage)


@main.command()
@click.argument("hash")
def stat(hash: str):
    hashH = Hash(hash)
    st = blob_stat(hashH)
    print(json.dumps(st))


@main.command()
@click.argument("hash")
def cat(hash: str):
    hashH = Hash(hash)
    op = blob_open(hashH)
    shutil.copyfileobj(op, sys.stdout.buffer)


@main.command()
@click.argument("hash")
def find(hash: str):
    hashH = Hash(hash)
    for found in blob_find(hashH):
        print(found)


@main.command()
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
def hashfile(filenames):
    for file in filenames:
        hash = hashit(file)
        print(hash)


@main.command()
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
def put(filenames):
    for file in filenames:
        if (
            hash := FileStorage(
                os.environ.get("BLOBBER_PUT_PATH", "~/.local/share/blobber/")
            )
            << file
        ):
            print(hash)


@main.command()
def print_len():
    for storage in get_storages():
        print(len(storage), storage)


@main.command()
@click.argument("hash")
def in_storage(hash: str):
    hashH = Hash(hash)
    for storage in get_storages():
        if hashH in storage:
            print(storage)


if __name__ == "__main__":
    main()
