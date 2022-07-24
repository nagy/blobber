import base64
import hashlib
import json
import os
import shutil
import sys
from abc import ABC, abstractmethod
from functools import cached_property

import click


class Hash(str):
    @cached_property
    def name(self):
        return self[44:]

    @cached_property
    def hash(self):
        return self[:43]

    @cached_property
    def as_path(self):
        return self[0:2] + "/" + self[2:4] + "/" + self

    @cached_property
    def only_path(self):
        return self[0:2] + "/" + self[2:4] + "/"


class Storage(ABC):
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def open(self, hash: Hash):
        pass

    @abstractmethod
    def stat(self, hash: Hash):
        pass

    @abstractmethod
    def exists(self, hash: Hash) -> bool:
        pass

    @abstractmethod
    def find(self, hash: Hash) -> [Hash]:
        pass


class FileStorage(Storage):
    def open(self, hash: Hash):
        return open(self.hashpath(hash), "rb")

    def stat(self, hash: Hash):
        return os.stat(self.hashpath(hash))

    def exists(self, hash: Hash) -> bool:
        return os.path.exists(self.hashpath(hash))

    def find(self, hash: Hash) -> [Hash]:
        if not os.path.exists(self.hashonlypath(hash)):
            for el in self.list():
                if hash in el:
                    yield el
        else:
            for file in os.listdir(self.hashonlypath(hash)):
                if file.startswith(hash):
                    yield Hash(file)

    def list(self):
        for currentpath, folders, files in os.walk(self.path):
            for file in files:
                yield Hash(file)

    def hashonlypath(self, hash: Hash) -> str:
        return os.path.expanduser(self.path) + "/" + hash.only_path

    def hashpath(self, hash: Hash) -> str:
        return os.path.expanduser(self.path) + "/" + hash.as_path

    def __repr__(self):
        return f"<FileStorage {self.path}>"


def get_paths() -> list[str]:
    return list(filter(None, os.getenv("BLOBBER_PATH", "").split(":")))


def get_storages() -> list[Storage]:
    ret = [FileStorage("~/.local/share/blobber/")]
    for p in get_paths():
        if p.endswith("/") and os.path.isdir(p):
            ret.append(FileStorage(p))
    return ret


def get_blobs() -> [Hash]:
    for storage in get_storages():
        for hash in storage.list():
            yield hash


def blob_open(arg: Hash):
    for storage in get_storages():
        if storage.exists(arg):
            return storage.open(arg)
    raise FileNotFoundError(arg)


def blob_stat(arg: Hash):
    for storage in get_storages():
        if storage.exists(arg):
            return storage.stat(arg)
    raise FileNotFoundError(arg)


def blob_find(arg: Hash) -> Hash:
    for storage in get_storages():
        if fnd := storage.find(arg):
            return fnd
    raise FileNotFoundError(arg)


@click.group()
def main():
    pass


@main.command()
def list_paths():
    for path in get_paths():
        print(path)


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
@click.argument("filename")
def hashfile(filename):
    sha = hashlib.sha256()
    with open(filename, "rb") as f:
        while n := f.read(128 * 1024):
            sha.update(n)
        hash = (
            base64.b64encode(sha.digest()).decode().replace("/", "_").replace("=", "")
        )
        basename = os.path.basename(filename)
        print(hash + "-" + basename)


if __name__ == "__main__":
    main()
