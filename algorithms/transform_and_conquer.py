"""Transform-and-conquer partition algorithm."""

from __future__ import annotations

from typing import Union

from core.validation import validate_partition_input

Number = Union[int, float]


def partition_transform_and_conquer(A: list[Number]) -> int:
    """Partition ``A`` stably with auxiliary negative and positive lists."""
    validate_partition_input(A)
    negatives = [value for value in A if value < 0]
    positives = [value for value in A if value > 0]
    A[:] = negatives + positives
    return len(negatives)
