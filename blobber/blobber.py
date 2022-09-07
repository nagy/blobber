import base64
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile
from typing import Iterator, List

from .hash import Hash
from .storage import FileStorage, Storage


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
