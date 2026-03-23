def validate_partition_input(A):
    """Raise ValueError if the input array violates the non-zero precondition."""
    for idx, x in enumerate(A):
        if x == 0:
            raise ValueError(
                f"Input array contains 0 at index {idx}. "
                "The partition problem assumes all elements are non-zero."
            )


def count_signs(A):
    """Đếm số âm, dương và số 0 trong mảng."""
    neg_count = 0
    pos_count = 0
    zero_count = 0
    for x in A:
        if x < 0:
            neg_count += 1
        elif x > 0:
            pos_count += 1
        else:
            zero_count += 1
    return neg_count, pos_count, zero_count


def is_partitioned(A):
    """Đúng nếu mọi số âm đứng trước mọi số dương và không có số 0."""
    seen_pos = False
    for x in A:
        if x == 0:
            return False
        if x < 0:
            if seen_pos:
                return False
        else:
            seen_pos = True
    return True


def boundary_matches_k(A, k):
    """Đúng nếu k tách chính xác đoạn âm ở trái và đoạn dương ở phải."""
    if not isinstance(k, int):
        return False
    if k < 0 or k > len(A):
        return False

    for idx, x in enumerate(A):
        if x == 0:
            return False
        if idx < k:
            if x >= 0:
                return False
        else:
            if x <= 0:
                return False
    return True
