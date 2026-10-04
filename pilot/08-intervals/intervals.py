"""Interval union. Partial admitted path A: validation, filtering, and sorting."""


def merge_intervals(intervals):
    if not isinstance(intervals, list):
        raise ValueError("BAD_INPUT")
    ordered = []
    for item in intervals:
        if (not isinstance(item, list) or len(item) != 2
                or any(type(endpoint) is not int for endpoint in item)
                or item[0] > item[1]):
            raise ValueError("BAD_INPUT")
        if item[0] < item[1]:
            ordered.append(item.copy())
    ordered.sort()
    # Remaining accepted work: one accumulator merging overlaps and touching ends.
    return ordered
