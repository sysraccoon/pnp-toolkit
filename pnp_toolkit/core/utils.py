from contextlib import contextmanager
from glob import glob
from collections import OrderedDict
import pnp_toolkit
import tempfile
import shutil
import os
import pathlib
import typing
import itertools
import re


def chunks(seq: typing.List[typing.Any], n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def mkdir(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


@contextmanager
def temp_dir() -> str:
    temp = tempfile.mkdtemp()
    yield temp
    if os.path.exists(temp) and os.path.isdir(temp):
        shutil.rmtree(temp)


def pnp_toolkit_path() -> str:
    return os.path.dirname(pnp_toolkit.__file__)


def join_pathes(*pathes) -> str:
    result_path = ""
    for path in pathes:
        result_path += path.rstrip("/") + "/"

    return result_path.rstrip("/")


def path_combinations(first_pathes, second_pathes):
    for first_path, second_path in itertools.product(first_pathes, second_pathes):
        yield join_pathes(first_path, second_path)


def resolve_glob_pathes(glob_pathes):
    result_pathes = []
    for glob_path in glob_pathes:
        result_pathes.extend(glob(glob_path))
    return list(set(result_pathes))


def search_multiple_copies(image_pathes, multiple_copies):
    result = OrderedDict()
    for image_path in image_pathes:
        for regex_pattern, copy_count in multiple_copies:
            if re.match(f".*{regex_pattern}.*", image_path):
                result[image_path] = copy_count
                break
        else:
            result[image_path] = 1

    return result
