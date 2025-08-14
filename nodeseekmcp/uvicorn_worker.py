# https://www.uvicorn.org/deployment/#gunicorn
# https://github.com/benoitc/gunicorn/issues/1539
from __future__ import annotations

from uvicorn_worker import UvicornWorker


class MyUvicornWorker(UvicornWorker):
    pass
