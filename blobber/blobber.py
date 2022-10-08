import io
import os
from functools import cached_property
from typing import Iterator, List, Optional
from zipfile import ZipFile

from .hash import Hash
from .storage import FileStorage, MetaStorage, Storage


class Bookmarks:
    def resolve(self, hash: Hash) -> Hash:
        if hash.isdigit():
            return self.by_num(int(hash))
        if resolved := self.by_name(hash):
            return resolved
        return hash

    def by_num(self, num: int) -> Hash:
        return Hash(self.lines[num - 1].split(" ")[0])

    def by_name(self, hash: Hash) -> Optional[Hash]:
        for line in self.lines:
            if hash in line[Hash.HASHLEN + 1 :].split(" "):
                return Hash(line.split(" ")[0])

    def __getitem__(self, nam) -> Optional[Hash]:
        return (
            self.by_num(nam)
            if (type(nam) == int or (type(nam) == str) and nam.is_digit())
            else self.by_name(nam)
        )

    @cached_property
    def lines(self):
        return (
            open(os.path.expanduser("~/.local/share/blobber_bookmarks"))
            .read()
            .split("\n")
        )


BM = Bookmarks()


def get_storages() -> List[Storage]:
    ret: List[Storage] = [
        FileStorage("~/.local/share/blobber/"),
        FileStorage("/var/lib/blobber/"),
    ]
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


def blob_stat(arg: Hash) -> List[int]:
    for storage in get_storages():
        if arg in storage:
            return storage.stat(arg)
    if parent := MetaStorage().find_parent(arg):
        parent_hash = parent[0]
        parent_index = parent[1]
        return blob_stat_child(parent_hash, parent_index)
    raise FileNotFoundError(arg)


def blob_open_child(parent: Hash, index: int) -> io.BytesIO:
    if found := next(blob_find(parent)):
        for storage in get_storages():
            if found in storage:
                zf = ZipFile(storage[found])
                ch = zf.filelist[index]
                return io.BytesIO(zf.open(ch).read())
    raise FileNotFoundError(parent)


def blob_stat_child(parent: Hash, index: int) -> List[int]:
    if found := next(blob_find(parent)):
        for storage in get_storages():
            if found in storage:
                zf = ZipFile(storage[found])
                ch = zf.filelist[index]
                return [0, 0, 0, 0, 0, 0, ch.file_size]
    raise FileNotFoundError(parent)
