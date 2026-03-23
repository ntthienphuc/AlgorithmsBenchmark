"""Divide-and-conquer partition algorithm."""

from __future__ import annotations

from typing import Union

from core.validation import validate_partition_input

Number = Union[int, float]


def _merge_signs(A: list[Number], left: int, mid: int, right: int) -> None:
    merged: list[Number] = []

    for index in range(left, mid + 1):
        if A[index] < 0:
            merged.append(A[index])
    for index in range(mid + 1, right + 1):
        if A[index] < 0:
            merged.append(A[index])
    for index in range(left, mid + 1):
        if A[index] > 0:
            merged.append(A[index])
    for index in range(mid + 1, right + 1):
        if A[index] > 0:
            merged.append(A[index])

    A[left : right + 1] = merged


def _partition_range(A: list[Number], left: int, right: int) -> None:
    if left >= right:
        return

    mid = (left + right) // 2
    _partition_range(A, left, mid)
    _partition_range(A, mid + 1, right)
    _merge_signs(A, left, mid, right)


def partition_divide_and_conquer(A: list[Number]) -> int:
    """Partition ``A`` with a stable divide-and-conquer merge process."""
    validate_partition_input(A)
    if A:
        _partition_range(A, 0, len(A) - 1)
    return sum(1 for value in A if value < 0)
