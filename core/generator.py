def _next_state(state: int) -> int:
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def _next_unit(state: int) -> tuple[int, float]:
    state = _next_state(state)
    return state, state / 0x80000000


def _shuffle_in_place(values: list[float], state: int) -> int:
    for index in range(len(values) - 1, 0, -1):
        state, unit = _next_unit(state)
        swap_index = int(unit * (index + 1))
        values[index], values[swap_index] = values[swap_index], values[index]
    return state


def gen_array(n: int, seed: int, neg_ratio: float = 0.5):
    """Sinh mảng n số thực khác 0, có tỷ lệ âm xấp xỉ neg_ratio."""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n phải là số nguyên dương.")
    if not (0.0 <= neg_ratio <= 1.0):
        raise ValueError("neg_ratio phải nằm trong [0, 1].")

    state = int(seed) & 0x7FFFFFFF
    values = []
    for _ in range(n):
        state, unit_1 = _next_unit(state)
        magnitude = round(0.1 + unit_1 * 99.9, 6)
        state, unit_2 = _next_unit(state)
        values.append(-magnitude if unit_2 < neg_ratio else magnitude)

    _shuffle_in_place(values, state)
    return values
