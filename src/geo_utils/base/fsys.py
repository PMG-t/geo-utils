import os
import sys
import shutil
import hashlib
import datetime
import tempfile
from typing import Optional, Tuple, Dict, List

from .import s3
from .log import Logger



_USE_EXCEPTIONS: bool = True
_DEFAULT_TEMP_DIR: Optional[str] = None


_additional_exts: Dict[str, Tuple[str, ...]] = {
    'shp': ("dbf", "shx", "prj", "cpg"),
    'tif': ("tfw", "jgw", "pwg")
}



def file_additional_extensions(filename: str) -> Tuple[str, ...]:
    """
    Returns a tuple of additional file extensions related to the given filename's extension.

    Args:
        filename (str): The filename to check.

    Returns:
        Tuple[str, ...]: Related extensions or an empty tuple.
    """
    ext = justext(filename)
    if ext in _additional_exts:
        return _additional_exts[ext]
    return tuple()


def python_path() -> str:
    """
    Returns the directory of the Python executable.

    Args:
        None

    Returns:
        str: Path to the Python executable's directory.
    """
    pathname, _ = os.path.split(normpath(sys.executable))
    return pathname


def normpath(pathname: str) -> str:
    """
    Normalizes a file path to use forward slashes.

    Args:
        pathname (str): The path to normalize.

    Returns:
        str: Normalized path.
    """
    if not pathname:
        return ""
    return os.path.normpath(pathname.replace("\\", "/")).replace("\\", "/")


def juststem(pathname: str) -> str:
    """
    Returns the filename without the extension.

    Args:
        pathname (str): The file path.

    Returns:
        str: Filename without extension.
    """
    pathname = os.path.basename(pathname)
    root, _ = os.path.splitext(pathname)
    return root


def justpath(pathname: str, n: int = 1) -> str:
    """
    Returns the path n directories above the given path.

    Args:
        pathname (str): Starting path.
        n (int): Number of directories to go up.

    Returns:
        str: Higher-level path.
    """
    for _ in range(n):
        pathname, _ = os.path.split(normpath(pathname))
    if pathname == "":
        return "."
    return normpath(pathname)


def justfname(pathname: str) -> str:
    """
    Returns the basename of the file from a path.

    Args:
        pathname (str): Full file path.

    Returns:
        str: Basename.
    """
    return normpath(os.path.basename(normpath(pathname)))


def justext(pathname: str) -> str:
    """
    Returns the file extension without the dot.

    Args:
        pathname (str): Pathname of the file.

    Returns:
        str: File extension.
    """
    pathname = os.path.basename(normpath(pathname))
    _, ext = os.path.splitext(pathname)
    return ext.lstrip(".")


def forceext(pathname: str, newext: str) -> str:
    """
    Forces a new extension on a pathname.

    Args:
        pathname (str): Original pathname.
        newext (str): New extension (without dot).

    Returns:
        str: Updated pathname with new extension.
    """
    root, _ = os.path.splitext(normpath(pathname))
    pathname = root + ("." + newext if len(newext.strip()) > 0 else "")
    return normpath(pathname)


def set_tempdir(base_dir: Optional[str] = None, dir_name: Optional[str] = None) -> str:
    """
    Sets the base temporary directory, optionally with a subdirectory.

    Args:
        base_dir (Optional[str]): Base directory to use.
        dir_name (Optional[str]): Optional subdirectory name.

    Returns:
        str: Path to the created temporary directory.
    """
    global _DEFAULT_TEMP_DIR
    if base_dir is not None:
        _DEFAULT_TEMP_DIR = normpath(base_dir)
    else:
        _DEFAULT_TEMP_DIR = tempfile.gettempdir()
    if dir_name is not None:
        _DEFAULT_TEMP_DIR = os.path.join(_DEFAULT_TEMP_DIR, dir_name)
    os.makedirs(_DEFAULT_TEMP_DIR, exist_ok=True)
    return _DEFAULT_TEMP_DIR


def tempdir(suffix: str = "") -> str:
    """
    Returns the path to a temporary directory with an optional suffix.

    Args:
        suffix (str): Suffix to add to the directory name.

    Returns:
        str: Full path to the temporary directory.
    """
    td = _DEFAULT_TEMP_DIR if _DEFAULT_TEMP_DIR is not None else tempfile.gettempdir()
    res = f"{td}/{suffix}"
    os.makedirs(res, exist_ok=True)
    return res


def tempfilename(temp_dir: Optional[str] = None, prefix: str = "", suffix: str = "") -> str:
    """
    Generates a unique temporary filename.

    Args:
        temp_dir (Optional[str]): Base temporary directory.
        prefix (str): Prefix for the filename.
        suffix (str): Suffix for the filename.

    Returns:
        str: Full path to the temporary file.
    """
    temp_dir = temp_dir if temp_dir is not None else tempdir()
    return normpath(temp_dir + "/" + datetime.datetime.strftime(datetime.datetime.now(), f"{prefix}%Y%m%d%H%M%S%f{suffix}"))


def hive_path(hive_dict: Dict[str, str]) -> str:
    """
    Converts a dictionary into a hive-style path string (key==value/key==value).

    Args:
        hive_dict (Dict[str, str]): Dictionary to convert.

    Returns:
        str: Hive-style string path.
    """
    return '/'.join([f"{k}=={v}" for k, v in hive_dict.items()])
