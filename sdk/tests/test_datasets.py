"""Datasets sub-client tests. Fixtures mirror the endpoint contract the API serves."""
from __future__ import annotations

import io
import json

import httpx
import pandas as pd
import pytest

from nyquist import NyquistError

from .conftest import make_client

# ── upload ────────────────────────────────────────────────────────────────


def test_upload_dataframe_serializes_parquet_multipart():
    """41-01-SUMMARY POST /api/datasets — multipart, 201 metadata response."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["content_type"] = request.headers.get("content-type", "")
        seen["body"] = request.content
        return httpx.Response(
            201,
            json={
                "id": "abc123",
                "name": "prices",
                "format": "parquet",
                "version": 1,
                "rows": 3,
                "cols": 2,
                "size_bytes": 512,
                "storage_backend": "local",
                "created_at": "2026-07-12T00:00:00Z",
            },
        )

    df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    out = make_client(handler).datasets.upload(df, name="prices")

    assert seen["path"] == "/api/datasets"
    assert seen["content_type"].startswith("multipart/form-data")
    assert b"prices.parquet" in seen["body"] or b"filename=" in seen["body"]
    assert out["id"] == "abc123"
    assert out["format"] == "parquet"


def test_upload_path_reads_csv_file(tmp_path):
    """upload(str) reads a local CSV/parquet file and posts it as-is."""
    csv_path = tmp_path / "signals.csv"
    csv_path.write_text("x,y\n1,2\n3,4\n")
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content_type"] = request.headers.get("content-type", "")
        seen["body"] = request.content
        return httpx.Response(
            201,
            json={
                "id": "csv-1", "name": "signals", "format": "csv", "version": 1,
                "rows": 2, "cols": 2, "size_bytes": 20, "storage_backend": "local",
                "created_at": "2026-07-12T00:00:00Z",
            },
        )

    out = make_client(handler).datasets.upload(str(csv_path))
    assert seen["content_type"].startswith("multipart/form-data")
    assert b"x,y" in seen["body"]
    assert out["format"] == "csv"


def test_upload_rejects_unsupported_extension(tmp_path):
    bad_path = tmp_path / "data.json"
    bad_path.write_text("{}")

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("should not be called")

    with pytest.raises(ValueError):
        make_client(handler).datasets.upload(str(bad_path))


# ── list / get / delete ─────────────────────────────────────────────────


def test_list_returns_dataframe_of_metadata_rows():
    """41-01-SUMMARY GET /api/datasets -> {datasets: [...], total}."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/datasets"
        return httpx.Response(
            200,
            json={
                "datasets": [
                    {
                        "id": "a1", "name": "prices", "format": "parquet",
                        "version": 1, "rows": 10, "cols": 5, "size_bytes": 100,
                        "storage_backend": "s3", "created_at": "2026-07-12T00:00:00Z",
                    },
                ],
                "total": 1,
            },
        )

    df = make_client(handler).datasets.list()
    assert len(df) == 1
    assert df.iloc[0]["id"] == "a1"


def test_list_empty_returns_empty_safe_dataframe():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"datasets": [], "total": 0})

    df = make_client(handler).datasets.list()
    assert df.empty


def test_get_returns_metadata_dict():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/datasets/a1"
        return httpx.Response(
            200,
            json={
                "id": "a1", "name": "prices", "format": "parquet", "version": 1,
                "rows": 10, "cols": 5, "size_bytes": 100, "storage_backend": "s3",
                "created_at": "2026-07-12T00:00:00Z",
            },
        )

    out = make_client(handler).datasets.get("a1")
    assert out["id"] == "a1"


def test_delete_returns_deleted_envelope():
    """41-01-SUMMARY DELETE /api/datasets/{id} -> {deleted: true, id}."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/api/datasets/a1"
        return httpx.Response(200, json={"deleted": True, "id": "a1"})

    out = make_client(handler).datasets.delete("a1")
    assert out == {"deleted": True, "id": "a1"}


# ── load (round-trip) ────────────────────────────────────────────────────


def test_load_parquet_round_trips_byte_identical_dataframe():
    """upload -> load returns the SAME DataFrame (41-04 success criterion)."""
    original = pd.DataFrame({"a": [1, 2, 3], "b": [4.5, 5.5, 6.5]})
    buf = io.BytesIO()
    original.to_parquet(buf, index=False)
    parquet_bytes = buf.getvalue()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/datasets/a1":
            return httpx.Response(
                200,
                json={
                    "id": "a1", "name": "prices", "format": "parquet", "version": 1,
                    "rows": 3, "cols": 2, "size_bytes": len(parquet_bytes),
                    "storage_backend": "local", "created_at": "2026-07-12T00:00:00Z",
                },
            )
        assert request.url.path == "/api/datasets/a1/data"
        return httpx.Response(
            200, content=parquet_bytes,
            headers={"content-type": "application/x-parquet"},
        )

    loaded = make_client(handler).datasets.load("a1")
    pd.testing.assert_frame_equal(loaded, original)


def test_datetime_index_survives_upload_load_roundtrip():
    """G-1 regression: the exact bytes upload() serialises must restore the
    DatetimeIndex on load(), so the research-loop join lines up ON the date
    index instead of collapsing to all-NaN. Composes the REAL serialize path
    (_df_to_parquet_bytes, used by upload) with the REAL load() deserialize —
    this fails under the old ``index=False``, which the mocked-transport
    tests never exercised.
    """
    from nyquist.datasets import _df_to_parquet_bytes

    idx = pd.date_range("2024-01-01", periods=30, freq="D", name="date")
    original = pd.DataFrame({"conviction": [0.6] * 30}, index=idx)
    parquet_bytes = _df_to_parquet_bytes(original)  # exactly what upload() POSTs

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/datasets/d1":
            return httpx.Response(
                200,
                json={
                    "id": "d1", "name": "my_signals", "format": "parquet",
                    "version": 1, "rows": 30, "cols": 1,
                    "size_bytes": len(parquet_bytes), "storage_backend": "local",
                    "created_at": "2026-07-12T00:00:00Z",
                },
            )
        assert request.url.path == "/api/datasets/d1/data"
        return httpx.Response(
            200, content=parquet_bytes,
            headers={"content-type": "application/x-parquet"},
        )

    back = make_client(handler).datasets.load("d1")
    assert isinstance(back.index, pd.DatetimeIndex)
    assert back.index.equals(idx)
    # the loop's join step now lines up instead of yielding an empty series
    px_close = pd.DataFrame({"close": range(100, 130)}, index=idx)
    joined = px_close.join(back, how="right")
    assert joined["close"].notna().all()


def test_load_csv_dispatches_on_metadata_format():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/datasets/c1":
            return httpx.Response(
                200,
                json={
                    "id": "c1", "name": "signals", "format": "csv", "version": 1,
                    "rows": 2, "cols": 2, "size_bytes": 20, "storage_backend": "local",
                    "created_at": "2026-07-12T00:00:00Z",
                },
            )
        assert request.url.path == "/api/datasets/c1/data"
        return httpx.Response(
            200, content=b"x,y\n1,2\n3,4\n", headers={"content-type": "text/csv"}
        )

    loaded = make_client(handler).datasets.load("c1")
    assert list(loaded.columns) == ["x", "y"]
    assert len(loaded) == 2


def test_load_data_4xx_raises_nyquist_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/datasets/missing":
            return httpx.Response(
                200,
                json={
                    "id": "missing", "name": "x", "format": "csv", "version": 1,
                    "rows": 0, "cols": 0, "size_bytes": 0, "storage_backend": "local",
                    "created_at": "2026-07-12T00:00:00Z",
                },
            )
        return httpx.Response(503, json={"detail": "Dataset storage unavailable"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).datasets.load("missing")
    assert exc.value.status_code == 503


# ── stateful research-loop sequence (Task 2 — mirrors the notebook) ────────


def test_research_loop_sequence_upload_load_var_save():
    """Mirrors 05_research_loop.ipynb call sequence end-to-end against one
    stateful mock: upload -> load -> risk.var-shaped compute -> reports.save.
    """
    store: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/datasets" and request.method == "POST":
            store["bytes"] = request.content
            return httpx.Response(
                201,
                json={
                    "id": "loop-1", "name": "my_signals", "format": "parquet",
                    "version": 1, "rows": 3, "cols": 1, "size_bytes": 64,
                    "storage_backend": "local", "created_at": "2026-07-12T00:00:00Z",
                },
            )
        if path == "/api/datasets/loop-1":
            return httpx.Response(
                200,
                json={
                    "id": "loop-1", "name": "my_signals", "format": "parquet",
                    "version": 1, "rows": 3, "cols": 1, "size_bytes": 64,
                    "storage_backend": "local", "created_at": "2026-07-12T00:00:00Z",
                },
            )
        if path == "/api/datasets/loop-1/data":
            buf = io.BytesIO()
            pd.DataFrame({"signal": [0.1, 0.2, 0.3]}).to_parquet(buf, index=False)
            return httpx.Response(
                200, content=buf.getvalue(),
                headers={"content-type": "application/x-parquet"},
            )
        if path == "/api/risk/var":
            assert json.loads(request.content)["returns"] == [0.1, 0.2, 0.3]
            return httpx.Response(200, json={"var": 0.02, "cvar": 0.03})
        if path == "/api/reports/save":
            body = json.loads(request.content)
            assert body["title"] == "My research"
            return httpx.Response(
                200,
                json={"saved": True, "key": "nyquist-reports/u1/2026/Q3/report_1.html"},
            )
        raise AssertionError(f"unexpected path {path}")

    nq = make_client(handler)
    my_df = pd.DataFrame({"signal": [0.1, 0.2, 0.3]})
    ds = nq.datasets.upload(my_df, name="my_signals")
    back = nq.datasets.load(ds["id"])
    pd.testing.assert_frame_equal(back, my_df)

    var_result = nq.risk.var(back["signal"].tolist())
    report = nq.reports.save(
        title="My research", returns=back["signal"].tolist(), metrics=var_result
    )
    assert report["key"] == "nyquist-reports/u1/2026/Q3/report_1.html"
