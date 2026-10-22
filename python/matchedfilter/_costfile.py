"""MF_COST_FILE: the JSON file of measured cost models and measured choices kept between
processes, and the one way it is read and written (a writer lock, then an atomic publish).
Every module that keeps something in the file goes through here."""
import json
import os
import tempfile
import warnings
from contextlib import contextmanager


def _cost_file():
    """MF_COST_FILE: a JSON file of measured cost models, for reproducible runs.

    Calibration times the engine, so under varying machine load two runs can
    measure different costs and choose different chains or budget splits --
    each within the false-dismissal budget, but not the same triggers near
    threshold. With MF_COST_FILE set, models are read from the file and any
    missing one is measured once and added; with the file populated and
    MF_AUTOTUNE=0 (no timed trials), the chain choice is deterministic.
    """
    from . import _config
    return _config.get("MF_COST_FILE")


#: Record-name prefixes of the trial format before 2026-10-21, which nothing reads now.
_LEGACY_PREFIXES = ("block-trial|", "chain-trial|", "q15-trial|")


#: (path, what) already warned about in this process.
_COST_WARNED = set()


def _cost_warn(path, what, msg):
    if (path, what) not in _COST_WARNED:
        _COST_WARNED.add((path, what))
        warnings.warn("MF_COST_FILE %s: %s" % (path, msg), RuntimeWarning, stacklevel=3)


def _read_cost_file(path):
    """(records, state): state is 'ok', 'missing' (no such file), 'damaged' (not a JSON
    object) or 'unreadable' (any other OSError); records is {} unless 'ok'."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return {}, "missing"
    except OSError:
        return {}, "unreadable"
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError:                  # (UnicodeDecodeError is a ValueError)
        return {}, "damaged"
    return (data, "ok") if isinstance(data, dict) else ({}, "damaged")


def _load_cost_file(path):
    """The records of the cost file at path ({} when missing). A damaged or unreadable
    file reads as empty, with a warning; trial records in the old format are reported
    once (tools/migrate_cost_file.py rewrites them)."""
    data, state = _read_cost_file(path)
    if state == "damaged":
        _cost_warn(path, state, "not a JSON object; read as empty (the next write keeps it "
                   "aside as %s.corrupt.<pid>)" % path)
    elif state == "unreadable":
        _cost_warn(path, state, "cannot be read; read as empty and never written")
    elif any(k.startswith(_LEGACY_PREFIXES) for k in data):
        _cost_warn(path, "legacy", "holds trial records in the format before 2026-10-21 "
                   "(block-trial|, chain-trial|, q15-trial|), which are not read; "
                   "python tools/migrate_cost_file.py %s rewrites them" % path)
    return data


def stored_choice(key, field="value"):
    """A measured per-machine choice kept in MF_COST_FILE (None without a file or entry);
    field names another part of its record (store_choice's extra fields).

    Measured choices -- a coarse kernel variant timed at first use, a fused batch's
    interleave depth, a chain or block-size trial -- are each valid, but made afresh per
    process they differ on noise, and borderline pairs then gate differently from run to
    run. Kept with the cost models, a machine makes each once and every later process
    reproduces it."""
    path = _cost_file()
    if path is None:
        return None
    rec = _load_cost_file(path).get("choice|" + key)
    return rec.get(field) if isinstance(rec, dict) else None


def store_choice(key, value, **extra):
    path = _cost_file()
    if path is not None:
        _store_cost(path, "choice|" + key, {"value": value, **extra})


@contextmanager
def _cost_file_lock(path):
    # Lock a stable sidecar: locking the JSON inode would stop protecting it as soon as
    # os.replace installs its successor. Keep the sidecar after releasing the lock.
    with open(os.fspath(path) + ".lock", "a+b") as lock:
        if os.name == "nt":
            import msvcrt
            if lock.seek(0, os.SEEK_END) == 0:
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _store_cost(path, skey, cm):
    """Merge one record under a writer lock, then publish atomically for unlocked readers."""
    value = cm.to_dict() if hasattr(cm, "to_dict") else cm
    _update_cost(path, skey, lambda old: value)


def _write_cost_file(path, data):
    """Publish data at path atomically (a temporary file in the same directory, then
    os.replace); the caller holds the writer lock."""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=os.path.dirname(path),
                                         prefix=os.path.basename(path) + ".",
                                         suffix=".tmp", delete=False) as f:
            tmp = f.name
            json.dump(data, f, indent=1, sort_keys=True)
        os.replace(tmp, path)
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)


def _update_cost(path, skey, merge):
    """Replace one record by merge(old record or None), read and written under the writer
    lock (so a record another process stored in between is seen); merge returns None to
    keep the record on file. Returns the record on file afterwards, or None when the file
    cannot be read: then nothing is written, so a file that is there but unreadable (EIO,
    a permission change, a stale NFS handle) is never replaced. A damaged file (not a
    JSON object) is kept aside as <path>.corrupt.<pid>, with a warning, before a fresh one
    is written."""
    path = os.path.abspath(os.fspath(path))
    with _cost_file_lock(path):
        data, state = _read_cost_file(path)
        if state == "unreadable":
            _cost_warn(path, state, "cannot be read; this record is not stored")
            return None
        if state == "damaged":
            aside = "%s.corrupt.%d" % (path, os.getpid())
            os.replace(path, aside)
            _cost_warn(path, "kept-aside", "not a JSON object; kept as %s and replaced by a "
                       "new file" % aside)
        value = merge(data.get(skey))
        if value is None:
            return data.get(skey)
        data[skey] = value
        _write_cost_file(path, data)
        return value


def _store_first(path, skey, value, valid=None):
    """Store value under skey unless a valid record is already on file (valid(record), or
    any record without valid), and return the record on file -- this process's value, or
    the one another process measured first, which the caller uses instead of its own, so
    every process sharing the file prices alike. Without a readable file: value."""
    def merge(old):
        if old is not None and (valid is None or valid(old)):
            return None
        return value
    on_file = _update_cost(path, skey, merge)
    return value if on_file is None else on_file
