"""Complete endpoint-event interval-union candidate, proposed for consolidation."""


def merge_intervals(intervals):
    if not isinstance(intervals, list):
        raise ValueError("BAD_INPUT")
    events = {}
    for item in intervals:
        if (not isinstance(item, list) or len(item) != 2
                or any(type(endpoint) is not int for endpoint in item)
                or item[0] > item[1]):
            raise ValueError("BAD_INPUT")
        start, end = item
        if start == end:
            continue
        events[start] = events.get(start, 0) + 1
        events[end] = events.get(end, 0) - 1
    coverage = 0
    opened = None
    merged = []
    for point in sorted(events):
        before = coverage
        coverage += events[point]
        if before == 0 and coverage > 0:
            opened = point
        elif before > 0 and coverage == 0:
            merged.append([opened, point])
    return merged
