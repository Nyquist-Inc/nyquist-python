"""Datasets sub-client — wraps ``/api/datasets``.

The "bring your own data" half of the research loop: ``nq.datasets.upload(df)``
in, the SAME DataFrame back via ``nq.datasets.load(dataset_id)``.
"""
from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Any

import pandas as pd

from .errors import NyquistError

if TYPE_CHECKING:
    from .client import Nyquist

_ALLOWED_FORMATS = {"csv", "parquet"}
_CONTENT_TYPES = {"csv": "text/csv", "parquet": "application/x-parquet"}


def _df_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to parquet bytes, preserving a meaningful index.

    Uses pandas' default ``index=None`` (NOT ``index=False``): a real index
    such as the ``DatetimeIndex`` returned by ``marketdata.history`` is
    written and restored on ``read_parquet`` (round-trip fidelity — the
    research loop joins the platform series against the uploaded frame ON
    that index), while a trivial ``RangeIndex`` is stored compactly in
    metadata rather than as an extra column. ``index=False`` silently dropped
    the index, so a same-length join fell through to all-NaN.
    """
    buf = io.BytesIO()
    df.to_parquet(buf)
    return buf.getvalue()


class Datasets:
    """Upload, list, fetch, load and delete the caller's own datasets.

    All calls are owner-scoped server-side; a stranger's dataset id always
    404s (never leaks existence).
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def upload(self, data: pd.DataFrame | str, name: str | None = None) -> dict[str, Any]:
        """Upload a DataFrame or a local CSV/parquet file path.

        A :class:`pandas.DataFrame` is serialised to parquet bytes in-memory
        (pyarrow, via ``df.to_parquet``); a ``str`` is treated as a path to
        an existing ``.csv``/``.parquet`` file and read from disk verbatim.
        Wraps ``POST /api/datasets`` (multipart/form-data: ``file`` +
        optional ``name`` form field). Returns the created dataset's
        metadata dict (``id, name, format, version, rows, cols, size_bytes,
        storage_backend, created_at``) — re-uploading the same ``name``
        does NOT overwrite, it inserts a new version.
        """
        if isinstance(data, pd.DataFrame):
            payload = _df_to_parquet_bytes(data)
            fmt = "parquet"
            filename = f"{name or 'dataset'}.parquet"
        else:
            path = data
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext not in _ALLOWED_FORMATS:
                raise ValueError(
                    f"unsupported file extension {ext!r} on {path!r} — "
                    "only .csv/.parquet are supported"
                )
            with open(path, "rb") as fh:
                payload = fh.read()
            fmt = ext
            filename = os.path.basename(path)

        files = {"file": (filename, payload, _CONTENT_TYPES[fmt])}
        form = {"name": name} if name else None
        return self._nq._request("POST", "/api/datasets", files=files, data=form)

    def list(self) -> pd.DataFrame:
        """The caller's own datasets as a DataFrame (empty-safe).

        Wraps ``GET /api/datasets`` — response shape ``{datasets: [...],
        total}``.
        """
        out = self._nq._request("GET", "/api/datasets")
        return pd.DataFrame(out.get("datasets", []))

    def get(self, dataset_id: str) -> dict[str, Any]:
        """Fetch one dataset's metadata.

        Wraps ``GET /api/datasets/{dataset_id}``.
        """
        return self._nq._request("GET", f"/api/datasets/{dataset_id}")

    def load(self, dataset_id: str) -> pd.DataFrame:
        """Fetch a dataset's underlying data back as a DataFrame.

        Reads the metadata first (to learn ``format``), then GETs
        ``/api/datasets/{dataset_id}/data`` as raw BYTES directly off the
        underlying ``httpx.Client`` (not through the JSON-shaping
        ``_request`` helper, which would mangle binary parquet content),
        and dispatches on format: ``parquet`` -> :func:`pandas.read_parquet`,
        ``csv`` -> :func:`pandas.read_csv`.
        """
        meta = self.get(dataset_id)
        resp = self._nq._client.get(f"/api/datasets/{dataset_id}/data")
        if resp.status_code >= 400:
            raise NyquistError(resp.status_code, _binary_detail(resp))
        buf = io.BytesIO(resp.content)
        if meta.get("format") == "parquet":
            return pd.read_parquet(buf)
        return pd.read_csv(buf)

    def delete(self, dataset_id: str) -> dict[str, Any]:
        """Delete a dataset (best-effort storage cleanup server-side).

        Wraps ``DELETE /api/datasets/{dataset_id}`` -> ``{deleted: true, id}``.
        """
        return self._nq._request("DELETE", f"/api/datasets/{dataset_id}")


def _binary_detail(resp: Any) -> str:
    """Extract a FastAPI ``{"detail": ...}`` message from a raw response.

    Mirrors ``client._detail`` — duplicated locally (not imported) to avoid
    a circular import between ``client.py`` and this module.
    """
    try:
        body = resp.json()
    except ValueError:
        return resp.text or resp.reason_phrase
    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"])
    return resp.text or resp.reason_phrase


__all__ = ["Datasets"]
