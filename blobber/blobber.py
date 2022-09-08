import base64
import hashlib
import io
import json
import os
import shutil
import sys
from typing import Iterator, List
from zipfile import ZipFile

from .hash import Hash
from .storage import FileStorage, Storage, MetaStorage


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


def blob_find(arg: Hash) -> Iterator[Hash]:
    for storage in get_storages():
        for fnd in storage.find(arg):
            yield fnd


def blob_open(arg: Hash) -> io.BufferedIOBase:
    for hash in blob_find(arg):
        for storage in get_storages():
            if hash in storage:
                return storage[hash]
    if parent := MetaStorage().find_parent(arg):
        parent_hash = parent[0]
        parent_index = parent[1]
        return blob_open_child(parent_hash, parent_index)
    raise FileNotFoundError(arg)


def blob_stat(arg: Hash):
    for storage in get_storages():
        if arg in storage:
            return storage.stat(arg)
    raise FileNotFoundError(arg)


def blob_open_child(parent: Hash, index: int) -> io.BytesIO:
    if found := next(blob_find(parent)):
        for storage in get_storages():
            if found in storage:
                zf = ZipFile(storage[found])
                ch = zf.filelist[index]
                return io.BytesIO(zf.open(ch).read())
    raise FileNotFoundError(parent)
