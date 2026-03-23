from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

PartitionFunction = Callable[..., int]


@dataclass(frozen=True)
class AlgorithmSpec:
    key: str
    display_name: str
    func: PartitionFunction
    needs_seed: bool
    strategy: str
    short_description: str
    time_complexity: str
    space_complexity: str
    in_place: bool
    stable: bool
    deterministic: bool

    @property
    def label(self) -> str:
        return self.display_name


@dataclass
class RunResult:
    algorithm: str
    n: int
    seed: int
    neg_ratio: float
    dataset_key: str
    batch_id: str
    run_kind: str
    runtime_us: int
    k: int
    neg_count: int
    pos_count: int
    partition_ok: bool
    k_ok: bool
    ok: bool
    array_file: str
    csv_file: str
    timestamp: str
