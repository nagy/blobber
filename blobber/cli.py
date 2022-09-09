import json
import os
import shutil
import sys
from zipfile import ZipFile

import click

from .blob import Blob
from . import __version__
from .blobber import (
    blob_find,
    blob_open,
    blob_stat,
    get_blobs,
    get_storages,
    blob_open_child,
)
from .hash import Hash, hashit
from .storage import FileStorage, MetaStorage


class HashParamType(click.ParamType):
    name = "hash"

    def convert(self, value, param, ctx):
        if isinstance(value, Hash):
            return value
        return self.convert(Hash(value), param, ctx)


class BlobParamType(click.ParamType):
    name = "blob"

    def convert(self, value, param, ctx):
        if isinstance(value, Blob):
            return value
        if isinstance(value, Hash):
            return self.convert(Blob(value), param, ctx)
        return self.convert(Hash(value), param, ctx)


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
@click.argument("hash", type=HashParamType())
def stat(hash: Hash):
    st = blob_stat(hash)
    print(json.dumps(st))


@main.command()
@click.argument("hash", type=HashParamType())
def cat(hash: Hash):
    op = blob_open(hash)
    shutil.copyfileobj(op, sys.stdout.buffer)


@main.command()
@click.argument("hash", type=HashParamType())
def find(hash: Hash):
    for found in blob_find(hash):
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
        putpath = os.environ.get("BLOBBER_PUT_PATH", "~/.local/share/blobber/")
        if hash := FileStorage(putpath) << file:
            print(hash)


@main.command()
def print_len():
    for storage in get_storages():
        print(len(storage), storage)


@main.command()
@click.argument("hash", type=HashParamType())
def children(hash: Hash):
    for ch in Blob(hash):
        print(ch)


@main.command()
@click.argument("hash", type=HashParamType())
def in_storage(hash: Hash):
    for storage in get_storages():
        if hash in storage:
            print(storage)


@main.command()
@click.argument("hash", type=HashParamType())
def zip_read(hash: Hash):
    if found := next(blob_find(hash)):
        for storage in get_storages():
            if found in storage:
                zf = ZipFile(storage[found])
                for ch in zf.filelist:
                    print(ch.filename)


@main.command()
@click.argument("hash", type=HashParamType())
@click.argument("index", type=click.INT)
def child_num_cat(hash: Hash, index: int):
    op = blob_open_child(hash, index)
    shutil.copyfileobj(op, sys.stdout.buffer)


@main.command()
@click.argument("blob", type=BlobParamType())
def meta(blob: Blob):
    print(json.dumps(blob.meta, indent=4 if sys.stdout.isatty() else None))


@main.command()
@click.argument("hash", type=HashParamType())
def parent(hash: Hash):
    if parent := MetaStorage().find_parent(hash):
        print(parent[0])


if __name__ == "__main__":
    main()
