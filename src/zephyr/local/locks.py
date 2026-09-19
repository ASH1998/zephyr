"""OS-owned leases release on exit; used independently by API and GPU worker."""
from pathlib import Path


def acquire_lock(path: Path):
    handle = path.open('a+b')
    try:
        if path.stat().st_size == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        if __import__('os').name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise
    return handle
