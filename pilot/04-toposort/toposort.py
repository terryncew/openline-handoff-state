"""toposort: JSON-lines DAG on stdin -> topological order on stdout. Spec: SPEC.md (frozen).

APPROACH B (admitted replacement for the superseded recursive DFS in
evidence/approach-a/): iterative Kahn's algorithm with a heap for the
lexicographic tie-break. No recursion anywhere.

MID-TASK STATE: parsing, ordering, tie-breaking, and 100k-node scale
work (4/5 tests pass). Cycle detection NOT implemented: on cyclic input
the current code emits the partial order and exits 0 instead of the
spec-required nonzero exit with CYCLE on stderr.
"""
import heapq
import json
import sys
from collections import defaultdict


def main():
    nodes = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            node, deps = obj["node"], obj["deps"]
        except (json.JSONDecodeError, KeyError, TypeError):
            sys.stderr.write("BAD_INPUT\n")
            return 1
        if not isinstance(node, str) or not isinstance(deps, list):
            sys.stderr.write("BAD_INPUT\n")
            return 1
        nodes[node] = deps
    indeg = {name: 0 for name in nodes}
    dependents = defaultdict(list)
    for name, deps in nodes.items():
        for dep in deps:
            if dep not in nodes:
                sys.stderr.write("BAD_INPUT\n")
                return 1
            indeg[name] += 1
            dependents[dep].append(name)
    heap = [name for name, deg in indeg.items() if deg == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        name = heapq.heappop(heap)
        out.append(name)
        for dependent in dependents[name]:
            indeg[dependent] -= 1
            if indeg[dependent] == 0:
                heapq.heappush(heap, dependent)
    # MID-TASK GAP: no cycle detection. A cyclic input leaves nodes
    # unemitted; the spec requires nonzero exit with CYCLE on stderr.
    sys.stdout.write("".join(name + "\n" for name in out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
