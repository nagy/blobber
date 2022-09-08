import base64
import hashlib
import io
import os
from functools import cached_property


class Hash(str):
    HASHLEN = 32

    @cached_property
    def name(self):
        return self[self.HASHLEN + 1 :]

    @cached_property
    def hash(self):
        return self[: self.HASHLEN]

    @cached_property
    def only_path(self):
        return self[0:2] + "/" + self[2:4] + "/"


def hashit(obj) -> Hash:
    sha = hashlib.sha256()
    if isinstance(obj, io.IOBase):
        while n := obj.read(128 * 1024):
            sha.update(n)
    else:
        with open(os.path.expanduser(obj), "rb") as f:
            while n := f.read(128 * 1024):
                sha.update(n)
    digest = sha.digest()[:20]
    hash = base64.b32encode(digest).decode().lower()
    if isinstance(obj, str):
        basename = os.path.basename(obj)
        if basename.startswith(hash):
            basename = basename[Hash.HASHLEN + 1 :]
        return Hash(hash + "-" + basename)
    else:
        return Hash(hash)
