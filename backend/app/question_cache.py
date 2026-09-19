"""Small, process-local cache for trusted Ask Data statistics."""

from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic


_MAX_ENTRIES = 8
_TTL_SECONDS = 30 * 60
_cache = OrderedDict()
_lock = Lock()


def get_question_stats(file_hash: str):
    """Return cached trusted statistics for a file hash, if still fresh."""
    now = monotonic()

    with _lock:
        entry = _cache.get(file_hash)

        if entry is None:
            return None

        created_at, question_stats = entry

        if now - created_at > _TTL_SECONDS:
            del _cache[file_hash]
            return None

        _cache.move_to_end(file_hash)
        return deepcopy(question_stats)


def cache_question_stats(file_hash: str, question_stats: dict) -> None:
    """Store only the trusted question statistics, with bounded memory use."""
    with _lock:
        _cache[file_hash] = (monotonic(), deepcopy(question_stats))
        _cache.move_to_end(file_hash)

        while len(_cache) > _MAX_ENTRIES:
            _cache.popitem(last=False)
