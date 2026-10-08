"""The multipart body of POST /bots: fields and files, checked by the upload rules of the SDK.

paths[i] is the path of files[i]; the file names of the parts do not count, since browsers
leave out the folders. The API only checks paths and sizes; the content is the runner's task
(E81, E92).
"""

import re
from dataclasses import dataclass

from flask import request
from sbm.analysis.upload import DEFAULT_ENTRY, MAX_PATH_LENGTH, UploadError, check_upload
from sbm_store import versions
from werkzeug.datastructures import MultiDict

from sbm_api.errors import invalid_parameter, invalid_upload

# The files may hold 2 MiB (verifikation.md); the rest is room for the multipart framing.
MAX_REQUEST_BYTES = 3 * 1024 * 1024
MAX_FILES = 200
LANGUAGES = ("python",)
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,31}")
TEXT_FIELDS = ("name", "version", "language", "entry", "paths")
FILES = "files"


@dataclass(frozen=True)
class Upload:
    name: str
    version: str
    language: str
    entry: str
    # (path, kind, content), in the order of the request.
    files: list[tuple[str, str, bytes]]


def parse_upload() -> Upload:
    request.max_content_length = MAX_REQUEST_BYTES
    if request.mimetype != "multipart/form-data":
        raise invalid_parameter("body", "the body must be multipart/form-data")
    form, uploaded = request.form, request.files
    # A text part named files is unknown too: the files must come as files.
    unknown = [field for field in form if field not in TEXT_FIELDS]
    unknown += [field for field in uploaded if field != FILES]
    if unknown:
        raise invalid_parameter(unknown[0], f"unknown field {unknown[0]}")
    name = _single(form, "name")
    if NAME.fullmatch(name) is None:
        raise invalid_parameter("name", "name must be 3 to 32 letters, digits, _ . or -")
    version = _single(form, "version")
    if versions.parse(version) is None:
        raise invalid_parameter("version", "version must be X.Y.Z, each part from 0 to 999")
    language = _single(form, "language")
    if language not in LANGUAGES:
        raise invalid_parameter("language", f"language must be one of {', '.join(LANGUAGES)}")
    entry = _single(form, "entry", DEFAULT_ENTRY)
    if len(entry) > MAX_PATH_LENGTH:
        raise invalid_parameter("entry", f"entry must be at most {MAX_PATH_LENGTH} characters")
    contents = [part.read() for part in uploaded.getlist(FILES)]
    return Upload(name, version, language, entry, _files(form.getlist("paths"), contents, entry))


def _single(form: MultiDict, field: str, default: str | None = None) -> str:
    values = form.getlist(field)
    if not values and default is not None:
        return default
    if len(values) != 1:
        raise invalid_parameter(field, f"{field} is required once")
    return values[0]


def _files(paths: list[str], contents: list[bytes], entry: str) -> list[tuple[str, str, bytes]]:
    if not 1 <= len(contents) <= MAX_FILES:
        raise invalid_parameter(FILES, f"send 1 to {MAX_FILES} files")
    if len(paths) != len(contents):
        raise invalid_parameter("paths", "send one path for each file")
    sizes = [(path, len(content)) for path, content in zip(paths, contents, strict=True)]
    try:
        checked = check_upload(sizes, entry)
    except UploadError as error:
        raise invalid_upload(str(error), error.path) from error
    return [
        (file.path, file.kind, content) for file, content in zip(checked, contents, strict=True)
    ]
