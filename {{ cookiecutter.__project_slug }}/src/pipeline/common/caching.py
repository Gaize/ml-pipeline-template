"""Fingerprints of source code, for cache keys that arguments alone would miss."""

import hashlib
import inspect
from typing import Any


def source_fingerprint(*objects: Any) -> str:
    """Return a hash of the source of each module, class, or function given.

    Pass the result as a step argument when a step's output depends on code its
    other arguments do not describe, so editing that code invalidates the cache.
    """
    digest = hashlib.sha256()
    for obj in objects:
        digest.update(inspect.getsource(obj).encode())
    return digest.hexdigest()
