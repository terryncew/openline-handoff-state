# toposort — frozen spec (2026-10-03)

Reads a DAG as JSON lines from stdin, writes a topological order to
stdout. Python 3 stdlib only. Single file: `toposort.py`.

## Input

One JSON object per line: `{"node": "<id>", "deps": ["<id>", ...]}`

- `deps` lists nodes that must come BEFORE `node`.
- Every dep id appears as a node line somewhere in the input.
- Node ids are strings. Input line order is arbitrary.
- Empty input → empty output.

## Output

One node id per line, a valid topological order:

- Every dep of a node appears on an earlier line than the node.
- Deterministic tie-breaking: among nodes with no remaining deps, emit
  the lexicographically smallest id first.

## Errors

- Cycle in input → nonzero exit, `CYCLE` on stderr. (stdout may be empty.)
- Malformed JSON line → nonzero exit, `BAD_INPUT` on stderr.

## Scale

Must handle 100,000 nodes without crashing. The implementation must not
depend on the recursion limit in any way.
