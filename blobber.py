import base64
import hashlib
import json
import os
import io
import shutil
import sys
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Iterator, List

import click


class Hash(str):
    @cached_property
    def name(self):
        return self[44:]

    @cached_property
    def hash(self):
        return self[:43]

    @cached_property
    def only_path(self):
        return self[0:2] + "/" + self[2:4] + "/"


class Storage(ABC):
    def __init__(self, path: str):
        self.path = os.path.expanduser(path)

    @abstractmethod
    def open(self, hash: Hash) -> io.BufferedReader:
        pass

    @abstractmethod
    def stat(self, hash: Hash):
        pass

    @abstractmethod
    def exists(self, hash: Hash) -> bool:
        pass

    @abstractmethod
    def find(self, hash: Hash) -> Iterator[Hash]:
        pass

    @abstractmethod
    def list(self) -> Iterator[Hash]:
        pass

    @abstractmethod
    def put(self, filename: str):
        pass

    def __len__(self) -> int:
        return len(list(self.list()))

    def __lshift__(self, other):
        return self.put(other)

    def __iter__(self):
        return self.list()

    def __contains__(self, other: Hash) -> bool:
        return self.exists(other)

    def __truediv__(self, other: Hash) -> io.BufferedReader:
        return self.open(other)

    def __str__(self):
        return self.path


class FileStorage(Storage):
    def __init__(self, path: str = "~/.local/share/blobber/"):
        super().__init__(path)

    def open(self, hash: Hash):
        return open(self.hashpath2(hash), "rb")

    def stat(self, hash: Hash):
        return os.stat(self.hashpath2(hash))

    def exists(self, hash: Hash) -> bool:
        return os.path.exists(self.hashpath2(hash))

    def find(self, hash: Hash) -> Iterator[Hash]:
        if not os.path.exists(self.hashonlypath(hash)):
            for el in self:
                if hash in el:
                    yield el
        else:
            for file in os.listdir(self.hashonlypath(hash)):
                if file.startswith(hash):
                    yield Hash(file)

    def list(self) -> Iterator[Hash]:
        for _currentpath, _folders, files in os.walk(self.path):
            for file in files:
                yield Hash(file)

    def hashonlypath(self, hash: Hash) -> str:
        return self.path + "/" + hash.only_path

    def hashpath2(self, hash: Hash) -> str:
        return self.path + "/" + hash

    def put(self, filename: str):
        hash = blob_hash2(filename)
        if hash not in self:
            newpath = self.path + "/" + hash
            shutil.copyfile(os.path.expanduser(filename), newpath)
            shutil.copystat(os.path.expanduser(filename), newpath)
            os.chmod(newpath, 0o444)
            return hash

    def __repr__(self):
        return f"<FileStorage {self.path}>"


def get_storages() -> List[Storage]:
    ret: List[Storage] = [FileStorage()]
    for p in os.getenv("BLOBBER_PATH", "").split(":"):
        if not p:
            continue
        if p.endswith("/") and os.path.isdir(p):
            ret.append(FileStorage(p))
    return ret


def get_blobs() -> Iterator[Hash]:
    for storage in get_storages():
        for hash in storage:
            yield hash


def blob_open(arg: Hash) -> io.BufferedReader:
    for storage in get_storages():
        if arg in storage:
            return storage / arg
    raise FileNotFoundError(arg)


def blob_stat(arg: Hash):
    for storage in get_storages():
        if arg in storage:
            return storage.stat(arg)
    raise FileNotFoundError(arg)


def blob_find(arg: Hash) -> Iterator[Hash]:
    for storage in get_storages():
        for fnd in storage.find(arg):
            yield fnd


def blob_hash(filename) -> Hash:
    sha = hashlib.sha256()
    with open(os.path.expanduser(filename), "rb") as f:
        while n := f.read(128 * 1024):
            sha.update(n)
        digest = sha.digest()
        hash = base64.b64encode(digest).decode()
        hash = hash.replace("/", "_").replace("=", "")
        basename = os.path.basename(filename)
        return Hash(hash + "-" + basename)


def blob_hash2(filename) -> Hash:
    sha = hashlib.sha256()
    with open(os.path.expanduser(filename), "rb") as f:
        while n := f.read(128 * 1024):
            sha.update(n)
        digest = sha.digest()[:20]
        hash = base64.b32encode(digest).decode().lower()
        basename = os.path.basename(filename)
        if basename.startswith(blob_hash(filename).hash + "-"):
            basename = basename[44:]
        if basename.startswith(hash):
            basename = basename[33:]
        return Hash(hash + "-" + basename)


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
        hash = blob_hash2(file)
        print(hash)


@main.command()
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
def put(filenames):
    for file in filenames:
        if hash := FileStorage("~/.local/share/blobber/") << file:
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
