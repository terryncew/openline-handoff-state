"""Interval union via admitted path A: validation, sorting, and accumulation."""


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
    merged = []
    for interval in ordered:
        if merged and interval[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], interval[1])
        else:
            merged.append(interval)
    return merged
