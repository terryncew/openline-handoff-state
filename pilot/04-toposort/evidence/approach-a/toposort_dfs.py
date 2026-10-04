"""APPROACH A — SUPERSEDED. Recursive DFS topological sort.

This was the first implementation attempt. It passes the small tests but
crashes with RecursionError on the 100,000-node chain fixture, violating
the frozen SPEC.md scale requirement ("must not depend on the recursion
limit in any way").

Kept as evidence. Do not resurrect: the admitted replacement is the
iterative Kahn's algorithm in toposort.py.
"""
import json
import sys


def main():
    nodes = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        nodes[obj["node"]] = obj["deps"]
    visited = {}
    out = []

    def visit(n):
        state = visited.get(n, 0)
        if state == 2:
            return
        if state == 1:
            raise ValueError("cycle")
        visited[n] = 1
        for dep in sorted(nodes[n]):
            visit(dep)
        visited[n] = 2
        out.append(n)

    try:
        for name in sorted(nodes):
            visit(name)
    except ValueError:
        sys.stderr.write("CYCLE\n")
        return 1
    sys.stdout.write("".join(name + "\n" for name in out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
