"""Minimal in-memory stand-in for the Motor calls the repositories make.

Supports equality filters on top-level fields and the update operators the code uses.
"""

from __future__ import annotations

import copy
from typing import Any

from pymongo import ReturnDocument


def _matches(doc: dict[str, Any], filt: dict[str, Any]) -> bool:
    return all(doc.get(k) == v for k, v in filt.items())


def _apply_update(doc: dict[str, Any], update: dict[str, Any], inserting: bool) -> None:
    for k, v in update.get("$set", {}).items():
        doc[k] = v
    for k, v in update.get("$inc", {}).items():
        doc[k] = doc.get(k, 0) + v
    if inserting:
        for k, v in update.get("$setOnInsert", {}).items():
            doc[k] = v


class _Cursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def sort(self, key: str, direction: int = 1) -> _Cursor:
        self._rows.sort(key=lambda d: d.get(key, 0), reverse=direction < 0)
        return self

    def __aiter__(self):
        self._it = iter(self._rows)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return copy.deepcopy(next(self._it))
        except StopIteration:
            raise StopAsyncIteration from None


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []

    def _find(self, filt: dict[str, Any]) -> dict[str, Any] | None:
        return next((d for d in self.docs if _matches(d, filt)), None)

    async def find_one(self, filt: dict[str, Any], projection: Any = None) -> dict[str, Any] | None:
        doc = self._find(filt)
        return copy.deepcopy(doc) if doc else None

    def find(self, filt: dict[str, Any] | None = None) -> _Cursor:
        return _Cursor([d for d in self.docs if _matches(d, filt or {})])

    async def insert_one(self, doc: dict[str, Any]) -> None:
        self.docs.append(copy.deepcopy(doc))

    async def replace_one(
        self, filt: dict[str, Any], doc: dict[str, Any], upsert: bool = False
    ) -> None:
        existing = self._find(filt)
        if existing is not None:
            self.docs.remove(existing)
            self.docs.append(copy.deepcopy(doc))
        elif upsert:
            self.docs.append(copy.deepcopy(doc))

    async def update_one(
        self, filt: dict[str, Any], update: dict[str, Any], upsert: bool = False
    ) -> None:
        doc = self._find(filt)
        if doc is not None:
            _apply_update(doc, update, inserting=False)
        elif upsert:
            new = dict(filt)
            _apply_update(new, update, inserting=True)
            self.docs.append(new)

    async def find_one_and_update(
        self,
        filt: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
        return_document: Any = ReturnDocument.BEFORE,
    ) -> dict[str, Any] | None:
        doc = self._find(filt)
        before = copy.deepcopy(doc)
        if doc is None:
            if not upsert:
                return None
            doc = dict(filt)
            _apply_update(doc, update, inserting=True)
            self.docs.append(doc)
        else:
            _apply_update(doc, update, inserting=False)
        return copy.deepcopy(doc) if return_document == ReturnDocument.AFTER else before

    async def create_index(self, *args: Any, **kwargs: Any) -> str:
        return "ok"


class FakeDB:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())


class FakeClient:
    def __init__(self) -> None:
        self.db = FakeDB()

    def __getitem__(self, name: str) -> FakeDB:
        return self.db

    def close(self) -> None:
        pass
