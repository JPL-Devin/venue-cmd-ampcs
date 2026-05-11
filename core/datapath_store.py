"""In-memory store for DataPath -> AMPCS sessionId mappings.

The VenueServer runs with a single Uvicorn worker, so a process-local dict
guarded by a threading lock is sufficient for safe concurrent access from the
FastAPI thread pool.
"""

import threading

_lock = threading.Lock()
_store: dict = {}  # data_path (str) -> session_id (int)


def set_datapath(data_path: str, session_id: int) -> None:
    with _lock:
        _store[data_path] = session_id


def get_session_id(data_path: str) -> int:
    with _lock:
        if data_path not in _store:
            raise KeyError(f'DataPath not found: {data_path}')
        return _store[data_path]


def delete_datapath(data_path: str) -> None:
    with _lock:
        if data_path not in _store:
            raise KeyError(f'DataPath not found: {data_path}')
        del _store[data_path]


def list_datapaths() -> dict:
    with _lock:
        return dict(_store)


def clear() -> None:
    """Reset the store. Intended for tests."""
    with _lock:
        _store.clear()
