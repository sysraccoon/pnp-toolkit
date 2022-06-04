from contextlib import contextmanager
import tempfile
import shutil
import os
import pathlib


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


@contextmanager
def temp_dir():
    temp = tempfile.mkdtemp()
    yield temp
    if os.path.exists(temp) and os.path.isdir(temp):
        shutil.rmtree(temp)

def join_pathes(*pathes):
    result_path = ""
    for path in pathes:
        result_path += path.rstrip("/") + "/"
    
    return result_path.rstrip("/")