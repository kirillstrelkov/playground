import hashlib
import os
import pickle
import tempfile

from utils.file import read_content, save_file


def get_hashsum(*args):
    m = hashlib.sha256()
    m.update(",".join([str(a) for a in args]).encode("utf-8"))
    return m.hexdigest()


def get_cached_value(hashsum, func_get_value, folder=None):
    if folder is None:
        folder = os.path.join(tempfile.gettempdir(), "locpycache")

    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, hashsum)

    if not os.path.exists(path):
        data = func_get_value()
        save_file(path, pickle.dumps(data), mode="wb", encoding=None)

    data = pickle.loads(read_content(path, mode="rb", encoding=None))
    if data is None:
        data = func_get_value()
        save_file(path, pickle.dumps(data), mode="wb", encoding=None)

    return data


def has_cached_value(hashsum, folder=None):
    if folder is None:
        folder = tempfile.gettempdir()

    path = os.path.join(folder, hashsum)

    return os.path.exists(path)
