import io
import os
import shutil
from abc import ABC, abstractmethod
from typing import Iterator, List

from .hash import Hash, hashit


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
        hash = hashit(filename)
        if hash not in self:
            newpath = self.path + "/" + hash
            shutil.copyfile(os.path.expanduser(filename), newpath)
            shutil.copystat(os.path.expanduser(filename), newpath)
            os.chmod(newpath, 0o444)
            return hash

    def __repr__(self):
        return f"<FileStorage {self.path}>"
