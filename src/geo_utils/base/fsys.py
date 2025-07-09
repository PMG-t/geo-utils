# -------------------------------------------------------------------------------
# License:
# Copyright (c) 2012-2022 Luzzi Valerio
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#
# Name:        filesystem.py
# Purpose:
#
# Author:      Luzzi Valerio
#
# Created:     16/12/2019
# -------------------------------------------------------------------------------

import os
import sys
import shutil
import hashlib
import datetime
import tempfile

from .import s3
from .log import Logger

_USE_EXCEPTIONS = True

_DEFAULT_TEMP_DIR = None

_additional_exts = {
    'shp': ("dbf", "shx", "prj", "cpg"),
    'tif': ("tfw", "jgw", "pwg")
}

def file_additional_extensions(filename):
    """
    file_additional_extensions
    """
    ext = justext(filename)
    if ext in _additional_exts:
        return _additional_exts[ext]
    return tuple()


def python_path():
    """
    python_path
    """
    pathname, _ = os.path.split(normpath(sys.executable))
    return pathname


def normpath(pathname):
    """
    normpath
    """
    if not pathname:
        return ""
    return os.path.normpath(pathname.replace("\\", "/")).replace("\\", "/")


def juststem(pathname):
    """
    juststem
    """
    pathname = os.path.basename(pathname)
    root, _ = os.path.splitext(pathname)
    return root


def justpath(pathname, n=1):
    """
    justpath
    """
    for _ in range(n):
        pathname, _ = os.path.split(normpath(pathname))
    if pathname == "":
        return "."
    return normpath(pathname)


def justfname(pathname):
    """
    justfname - returns the basename
    """
    return normpath(os.path.basename(normpath(pathname)))


def justext(pathname):
    """
    justext
    """
    pathname = os.path.basename(normpath(pathname))
    _, ext = os.path.splitext(pathname)
    return ext.lstrip(".")


def forceext(pathname, newext):
    """
    forceext
    """
    root, _ = os.path.splitext(normpath(pathname))
    pathname = root + ("." + newext if len(newext.strip()) > 0 else "")
    return normpath(pathname)


def set_tempdir(base_dir=None, dir_name=None):
    """
    set_tempdir
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


def tempdir(suffix=""):
    """
    tempdir
    """
    td = _DEFAULT_TEMP_DIR if _DEFAULT_TEMP_DIR is not None else tempfile.gettempdir()
    res = f"{td}/{suffix}"
    os.makedirs(res, exist_ok=True)
    return res


def tempfilename(temp_dir=None, prefix="", suffix=""):
    """
    return a temporary filename
    """
    temp_dir = temp_dir if temp_dir is not None else tempdir()
    return normpath(temp_dir + "/" + datetime.datetime.strftime(datetime.datetime.now(), f"{prefix}%Y%m%d%H%M%S%f{suffix}"))


def hive_path(hive_dict):
    return '/'.join([f"{k}=={v}" for k, v in hive_dict.items()])
