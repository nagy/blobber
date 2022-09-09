from functools import cached_property

from .storage import MetaStorage
from .hash import Hash


class Blob:
    def __init__(self, value: Hash):
        self.value = value

    @cached_property
    def meta(self):
        return MetaStorage().get(self.value)

    @cached_property
    def children(self):
        return self.meta.get("children", [])

    def __iter__(self):
        return iter(self.children)
