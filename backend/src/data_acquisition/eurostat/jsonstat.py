"""
JSON-stat 2.0 parsing helpers.

Eurostat Statistics API commonly returns JSON-stat 2.0 datasets.
We flatten observations into a list of records: one per combination of dimensions.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JsonStatDimension:
    id: str
    codes_by_pos: list[str]
    labels_by_code: dict[str, str]


def _get_dimension(dataset: dict[str, Any], dim_id: str) -> JsonStatDimension:
    dim = dataset["dimension"][dim_id]
    cat = dim["category"]

    # category.index can be list (pos->code) or dict (code->pos)
    index = cat.get("index")
    codes_by_pos: list[str]
    if isinstance(index, list):
        codes_by_pos = [str(x) for x in index]
    elif isinstance(index, dict):
        codes_by_pos_temp: list[str | None] = [None] * len(index)
        for code, pos in index.items():
            codes_by_pos_temp[int(pos)] = str(code)
        if any(c is None for c in codes_by_pos_temp):
            raise ValueError(f"Invalid JSON-stat category index for dimension {dim_id}")
        codes_by_pos = [c for c in codes_by_pos_temp if c is not None]
    else:
        raise ValueError(f"Unsupported JSON-stat category index for dimension {dim_id}")

    labels = cat.get("label", {}) or {}
    labels_by_code = {str(k): str(v) for k, v in labels.items()}
    return JsonStatDimension(
        id=dim_id, codes_by_pos=codes_by_pos, labels_by_code=labels_by_code
    )


def _value_to_list(dataset: dict[str, Any], total_size: int) -> list[Any]:
    """
    JSON-stat 'value' can be:
    - list with length == total_size
    - dict mapping index -> value (sparse)
    """
    value = dataset.get("value")
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        out = [None] * total_size
        for k, v in value.items():
            out[int(k)] = v
        return out
    raise ValueError("Unsupported JSON-stat 'value' type")


def flatten_jsonstat_dataset(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Flatten a JSON-stat dataset into records with dimension codes and a 'value'.
    """
    dim_ids: list[str] = [str(x) for x in dataset.get("id", [])]
    sizes: list[int] = [int(x) for x in dataset.get("size", [])]
    if not dim_ids or not sizes or len(dim_ids) != len(sizes):
        raise ValueError("Invalid JSON-stat dataset: missing/invalid id/size")

    dims = [_get_dimension(dataset, d) for d in dim_ids]
    total_size = 1
    for s in sizes:
        total_size *= s

    values = _value_to_list(dataset, total_size)
    if len(values) != total_size:
        raise ValueError("Invalid JSON-stat dataset: value length mismatch")

    # Precompute multipliers for linear index -> multidimensional indices.
    multipliers: list[int] = []
    prod = 1
    for s in reversed(sizes[1:]):
        prod *= s
        multipliers.append(prod)
    multipliers = [*list(reversed(multipliers)), 1]

    records: list[dict[str, Any]] = []
    for linear_idx, v in enumerate(values):
        if v is None:
            continue
        idx_remaining = linear_idx
        rec: dict[str, Any] = {}
        for dim, _size, mult in zip(dims, sizes, multipliers, strict=True):
            pos = idx_remaining // mult
            idx_remaining = idx_remaining % mult
            code = dim.codes_by_pos[pos]
            rec[dim.id] = code
            # Include labels where available for better downstream mapping.
            label = dim.labels_by_code.get(code)
            if label is not None:
                rec[f"{dim.id}__label"] = label
        rec["value"] = v
        records.append(rec)

    return records


_YEAR_RE = re.compile(r"(\d{4})")


def normalize_time_to_year(
    time_code: str | None, time_label: str | None = None
) -> int | None:
    if time_code:
        m = _YEAR_RE.search(time_code)
        if m:
            return int(m.group(1))
    if time_label:
        m = _YEAR_RE.search(time_label)
        if m:
            return int(m.group(1))
    return None


def normalize_sex(  # noqa: PLR0911
    code: str | None, label: str | None = None
) -> str | None:
    if code is None and label is None:
        return None
    c = (code or "").strip().upper()
    if c in {"M", "F"}:
        return c
    if c in {"T", "TOTAL"}:
        return "Total"
    # Fallback to label heuristics.
    lbl = (label or "").strip().lower()
    if lbl in {"male", "men"}:
        return "M"
    if lbl in {"female", "women"}:
        return "F"
    if lbl in {"total", "both sexes"}:
        return "Total"
    return c or None


def normalize_age(  # noqa: PLR0911
    code: str | None, label: str | None = None
) -> str | None:
    """
    Convert common Eurostat age codes into a string our DemographicNormalizer can parse.
    Examples:
      - Y0 -> "0"
      - Y0-4 -> "0-4"
      - Y_GE85 -> "85+"
      - TOTAL -> None (caller may treat as total)
    """
    if code is None and label is None:
        return None
    c = (code or "").strip().upper()
    if c in {"TOTAL", "T"}:
        return None
    if c.startswith("Y_GE"):
        try:
            return f"{int(c.replace('Y_GE', ''))}+"
        except ValueError:
            return label
    if c.startswith("Y_LT"):
        try:
            return f"under {int(c.replace('Y_LT', ''))}"
        except ValueError:
            return label
    if c.startswith("Y") and "-" in c:
        # Y5-9
        return c[1:].replace("_", "").lower()
    if c.startswith("Y") and c[1:].isdigit():
        return str(int(c[1:]))
    # Fallback to label (often "0-4" etc.)
    return label or code
