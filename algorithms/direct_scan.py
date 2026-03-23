"""Direct scan partition algorithm."""

from __future__ import annotations

from typing import Union

from core.validation import validate_partition_input

Number = Union[int, float]


def partition_direct_scan(A: list[Number]) -> int:
    """Partition ``A`` in place by scanning forward and swapping later negatives left."""
    validate_partition_input(A)
    n = len(A)
    for i in range(n):
        if A[i] < 0:
            continue
        j = i + 1
        while j < n and A[j] > 0:
            j += 1
        if j == n:
            break
        A[i], A[j] = A[j], A[i]
    return sum(1 for value in A if value < 0)
