"""Two-pointers partition algorithm."""

from __future__ import annotations

from typing import Union

from core.validation import validate_partition_input

Number = Union[int, float]


def partition_two_pointers(A: list[Number]) -> int:
    """Partition ``A`` in place with two opposing pointers."""
    validate_partition_input(A)
    left = 0
    right = len(A) - 1

    while left <= right:
        while left <= right and A[left] < 0:
            left += 1
        while left <= right and A[right] > 0:
            right -= 1
        if left < right:
            A[left], A[right] = A[right], A[left]
            left += 1
            right -= 1

    return left
