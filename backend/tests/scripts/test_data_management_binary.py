"""Unit tests for BYTEA <-> base64 dump/upload helpers (no DB required)."""

import base64
import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "data_management.py"
_SPEC = importlib.util.spec_from_file_location("data_management_script", _SCRIPT)
assert _SPEC and _SPEC.loader
dm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(dm)


class TestSerializeRowForDump:
    def test_encodes_bytes_and_memoryview(self):
        raw = b"\x89PNG\r\n"
        row = {
            "id": 1,
            "uuid": "abc",
            "data": memoryview(raw),
            "filename": "x.png",
        }
        out = dm._serialize_row_for_dump(row)
        assert out["_data_encoding"] == "base64"
        assert out["_binary_fields"] == ["data"]
        assert out["data"] == base64.b64encode(raw).decode("ascii")
        assert out["filename"] == "x.png"
        assert out["id"] == 1

    def test_no_marker_without_binary(self):
        out = dm._serialize_row_for_dump({"id": 1, "name": "tag"})
        assert "_data_encoding" not in out
        assert "_binary_fields" not in out


class TestPrepareRowForUpload:
    def test_decodes_base64_with_markers(self):
        raw = b"hello-image"
        row = {
            "id": 2,
            "data": base64.b64encode(raw).decode("ascii"),
            "_data_encoding": "base64",
            "_binary_fields": ["data"],
        }
        prepared = dm._prepare_row_for_upload("recipe_images", row)
        assert prepared is not None
        assert prepared["data"] == raw
        assert "_data_encoding" not in prepared
        assert "_binary_fields" not in prepared

    def test_skips_legacy_memory_placeholder(self):
        row = {"id": 3, "data": "<memory at 0x10a7b0b80>"}
        assert dm._prepare_row_for_upload("recipe_images", row) is None

    def test_heuristic_decode_for_recipe_images_without_marker(self):
        raw = b"png-bytes"
        row = {"id": 4, "data": base64.b64encode(raw).decode("ascii")}
        prepared = dm._prepare_row_for_upload("recipe_images", row)
        assert prepared is not None
        assert prepared["data"] == raw
