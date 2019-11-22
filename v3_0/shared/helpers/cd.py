import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def cd(new_path: Path):
    assert new_path.exists()
    assert new_path.is_dir()

    previous_path = Path.cwd()

    os.chdir(str(new_path.expanduser()))

    try:
        yield
    finally:
        os.chdir(str(previous_path))
