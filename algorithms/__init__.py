"""Official partition algorithms and academic metadata."""

from __future__ import annotations

from core.models import AlgorithmSpec

from algorithms.direct_scan import partition_direct_scan
from algorithms.divide_and_conquer import partition_divide_and_conquer
from algorithms.transform_and_conquer import partition_transform_and_conquer
from algorithms.two_pointers import partition_two_pointers


def _stable_text(value: bool) -> str:
    return "Stable" if value else "Unstable"


def _bool_text(value: bool) -> str:
    return "Yes" if value else "No"


OFFICIAL_ALGORITHM_SPECS = (
    AlgorithmSpec(
        key="direct_scan",
        display_name="Direct Scan",
        func=partition_direct_scan,
        needs_seed=False,
        strategy="Direct / Straightforward Method",
        short_description="Scan left to right; when a positive is found, search forward for the next negative and swap.",
        time_complexity="O(n^2)",
        space_complexity="O(1)",
        in_place=True,
        stable=False,
        deterministic=True,
    ),
    AlgorithmSpec(
        key="two_pointers",
        display_name="Two Pointers",
        func=partition_two_pointers,
        needs_seed=False,
        strategy="Direct Optimized / In-place Partition",
        short_description="Move two pointers inward and swap misplaced positive/negative pairs in place.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        in_place=True,
        stable=False,
        deterministic=True,
    ),
    AlgorithmSpec(
        key="transform_and_conquer",
        display_name="Transform-and-Conquer",
        func=partition_transform_and_conquer,
        needs_seed=False,
        strategy="Transform-and-Conquer",
        short_description="Build auxiliary negative and positive lists, then copy the transformed order back into the input array.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        in_place=False,
        stable=True,
        deterministic=True,
    ),
    AlgorithmSpec(
        key="divide_and_conquer",
        display_name="Divide-and-Conquer",
        func=partition_divide_and_conquer,
        needs_seed=False,
        strategy="Divide-and-Conquer",
        short_description="Recursively partition each half, then merge negatives first and positives after while preserving relative order.",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        in_place=False,
        stable=True,
        deterministic=True,
    ),
)

OFFICIAL_ALGORITHMS = [
    (spec.display_name, (spec.func, spec.needs_seed))
    for spec in OFFICIAL_ALGORITHM_SPECS
]
OFFICIAL_ALGORITHM_LABELS = [spec.display_name for spec in OFFICIAL_ALGORITHM_SPECS]
OFFICIAL_ALGORITHM_KEYS = [spec.key for spec in OFFICIAL_ALGORITHM_SPECS]
ALGORITHM_SPECS_BY_KEY = {spec.key: spec for spec in OFFICIAL_ALGORITHM_SPECS}
ALGORITHM_SPECS_BY_NAME = {spec.display_name: spec for spec in OFFICIAL_ALGORITHM_SPECS}
ALGORITHM_DETAILS = {
    spec.display_name: {
        "key": spec.key,
        "display_name": spec.display_name,
        "strategy": spec.strategy,
        "short_description": spec.short_description,
        "time_complexity": spec.time_complexity,
        "time": spec.time_complexity,
        "space_complexity": spec.space_complexity,
        "memory": spec.space_complexity,
        "in_place": spec.in_place,
        "in_place_text": _bool_text(spec.in_place),
        "stable": spec.stable,
        "stable_text": _stable_text(spec.stable),
        "deterministic": spec.deterministic,
        "deterministic_text": _bool_text(spec.deterministic),
        "function_name": spec.func.__name__,
    }
    for spec in OFFICIAL_ALGORITHM_SPECS
}
LEGACY_ALGORITHM_NAME_MAP = {
    "Trực tiếp (quét + đổi chỗ)": "Direct Scan",
    "Trực tiếp tối ưu (hai con trỏ)": "Two Pointers",
    "Biến đổi để trị": "Transform-and-Conquer",
    "Chia để trị": "Divide-and-Conquer",
}


def normalize_algorithm_name(name: str) -> str:
    """Return the canonical display name for current or legacy algorithm labels."""
    cleaned = (name or "").strip()
    if cleaned in ALGORITHM_SPECS_BY_NAME:
        return cleaned
    return LEGACY_ALGORITHM_NAME_MAP.get(cleaned, cleaned)


__all__ = [
    "ALGORITHM_DETAILS",
    "ALGORITHM_SPECS_BY_KEY",
    "ALGORITHM_SPECS_BY_NAME",
    "LEGACY_ALGORITHM_NAME_MAP",
    "OFFICIAL_ALGORITHMS",
    "OFFICIAL_ALGORITHM_KEYS",
    "OFFICIAL_ALGORITHM_LABELS",
    "OFFICIAL_ALGORITHM_SPECS",
    "normalize_algorithm_name",
    "partition_direct_scan",
    "partition_divide_and_conquer",
    "partition_transform_and_conquer",
    "partition_two_pointers",
]
