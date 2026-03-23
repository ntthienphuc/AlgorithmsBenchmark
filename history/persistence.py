import csv
import json
import os
import unicodedata
from datetime import datetime
import uuid

from algorithms import normalize_algorithm_name
from core.models import RunResult
from core.validation import boundary_matches_k, count_signs, is_partitioned

RESULTS_HEADER = [
    "timestamp",
    "algorithm",
    "n",
    "seed",
    "neg_ratio",
    "dataset_key",
    "batch_id",
    "run_kind",
    "runtime_us",
    "k",
    "neg_count",
    "pos_count",
    "partition_ok",
    "k_ok",
    "ok",
    "array_file",
]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _normalize_save_array_mode(save_array_mode: str):
    mode = (save_array_mode or "on_error").strip().lower()
    if mode in {"always", "never", "on_error"}:
        return mode
    return "on_error"


def normalize_neg_ratio(neg_ratio: float):
    return float(f"{float(neg_ratio):.6f}")


def make_dataset_key(seed: int, neg_ratio: float):
    return f"seed={int(seed)}|neg_ratio={normalize_neg_ratio(neg_ratio):.6f}"


def make_timestamp():
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:6]}"


def make_batch_id(run_kind: str = "single"):
    safe_kind = (run_kind or "single").strip().lower().replace(" ", "_")
    return f"{safe_kind}_{make_timestamp()}"


def _slugify_algorithm(algorithm: str):
    normalized = unicodedata.normalize("NFKD", algorithm).encode("ascii", "ignore").decode("ascii")
    chars = []
    for ch in normalized.lower():
        if ch.isalnum():
            chars.append(ch)
        else:
            chars.append("_")
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "algorithm"


def _read_existing_rows(csv_path: str):
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:
            rows.append([record.get(col, "") for col in RESULTS_HEADER])
    return rows


def _header_matches(csv_path: str):
    if not os.path.exists(csv_path):
        return False
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader, []) == RESULTS_HEADER


def save_run(
    output_dir: str,
    algorithm: str,
    n: int,
    seed: int,
    neg_ratio: float,
    runtime_us: int,
    A,
    k: int,
    batch_id: str = "",
    run_kind: str = "single",
    save_array_mode: str = "on_error",
) -> RunResult:
    ensure_dir(output_dir)
    algorithm = normalize_algorithm_name(algorithm)
    ts = make_timestamp()
    save_array_mode = _normalize_save_array_mode(save_array_mode)
    run_kind = (run_kind or "single").strip().lower()
    batch_id = (batch_id or make_batch_id(run_kind)).strip()
    dataset_key = make_dataset_key(seed, neg_ratio)
    neg_ratio = normalize_neg_ratio(neg_ratio)

    neg_count, pos_count, zero_count = count_signs(A)
    partition_ok = is_partitioned(A)
    k_ok = boundary_matches_k(A, k)
    ok = partition_ok and k_ok

    array_path = ""
    should_save_array = save_array_mode == "always" or (save_array_mode == "on_error" and not ok)
    if should_save_array:
        arrays_dir = os.path.join(output_dir, "arrays")
        ensure_dir(arrays_dir)
        safe_alg = _slugify_algorithm(algorithm)
        ratio_tag = str(neg_ratio).replace(".", "_")
        array_path = os.path.join(arrays_dir, f"array_{safe_alg}_n{n}_seed{seed}_r{ratio_tag}_{ts}.json")
        with open(array_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "algorithm": algorithm,
                    "n": n,
                    "seed": seed,
                    "neg_ratio": neg_ratio,
                    "dataset_key": dataset_key,
                    "batch_id": batch_id,
                    "run_kind": run_kind,
                    "k": k,
                    "neg_count": neg_count,
                    "pos_count": pos_count,
                    "zero_count": zero_count,
                    "partition_ok": partition_ok,
                    "k_ok": k_ok,
                    "ok": ok,
                    "array": A,
                },
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )

    csv_path = os.path.join(output_dir, "results.csv")
    row = [
        ts,
        algorithm,
        str(n),
        str(seed),
        f"{neg_ratio:.6f}",
        dataset_key,
        batch_id,
        run_kind,
        str(runtime_us),
        str(k),
        str(neg_count),
        str(pos_count),
        str(partition_ok),
        str(k_ok),
        str(ok),
        os.path.relpath(array_path, output_dir) if array_path else "",
    ]

    existing_rows = []
    mode = "a"
    if not os.path.exists(csv_path):
        mode = "w"
    elif not _header_matches(csv_path):
        existing_rows = _read_existing_rows(csv_path)
        mode = "w"

    with open(csv_path, mode, encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(RESULTS_HEADER)
            w.writerows(existing_rows)
        w.writerow(row)

    return RunResult(
        algorithm=algorithm, n=n, seed=seed, neg_ratio=neg_ratio,
        dataset_key=dataset_key, batch_id=batch_id, run_kind=run_kind,
        runtime_us=runtime_us, k=k, neg_count=neg_count, pos_count=pos_count,
        partition_ok=partition_ok, k_ok=k_ok, ok=ok,
        array_file=array_path, csv_file=csv_path, timestamp=ts,
    )


def load_history(csv_path: str):
    """Đọc results.csv -> list dict."""
    if not os.path.exists(csv_path):
        return []

    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                seed = int(r.get("seed", "0"))
                neg_ratio = normalize_neg_ratio(float(r.get("neg_ratio", "0")))
                algorithm = normalize_algorithm_name(r.get("algorithm", ""))
                partition_ok = (r.get("partition_ok", "").strip().lower() == "true")
                k_ok = (r.get("k_ok", "").strip().lower() == "true")
                ok_raw = r.get("ok", "").strip().lower()
                dataset_key = r.get("dataset_key", "").strip() or make_dataset_key(seed, neg_ratio)
                batch_id = r.get("batch_id", "").strip() or f"legacy_{r.get('timestamp', '').strip() or 'unknown'}"
                rows.append({
                    "timestamp": r.get("timestamp", ""),
                    "algorithm": algorithm,
                    "n": int(r.get("n", "0")),
                    "seed": seed,
                    "neg_ratio": neg_ratio,
                    "dataset_key": dataset_key,
                    "batch_id": batch_id,
                    "run_kind": r.get("run_kind", "").strip() or ("legacy" if batch_id.startswith("legacy_") else "single"),
                    "runtime_us": int(r.get("runtime_us", "0")),
                    "partition_ok": partition_ok,
                    "k_ok": k_ok,
                    "ok": (ok_raw == "true") if ok_raw else (partition_ok and k_ok),
                })
            except Exception:
                continue
    return rows
