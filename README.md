# msreliability

Exact reliability of multistate flow networks in Python.

Each edge of an undirected network has an independent random capacity
0, 1, ..., K. `msreliability` computes the exact distribution of the s-t
maximum flow, Pr(F = d) for every demand level d, in one state-space
decomposition. The reliability at level d is Pr(F >= d).

**Status: pre-alpha.** The Python reference implementation is exact and
tested against full enumeration. A compiled core, benchmarks and
documentation are planned (see [docs/ROADMAP.md](docs/ROADMAP.md)).

## Example

```python
import networkx as nx
from msreliability import capacity_distribution, reliability

G = nx.Graph()
G.add_edge("s", "a", pmf=[0.1, 0.2, 0.7])   # Pr(capacity = 0, 1, 2)
G.add_edge("a", "t", pmf=[0.1, 0.9])
G.add_edge("s", "t", pmf=[0.3, 0.7])

capacity_distribution(G, "s", "t")  # {0: ..., 1: ..., 2: ...}
reliability(G, "s", "t", d=2)        # Pr(max flow >= 2)
```

## Method

For a box of capacity vectors [L, U], let k be the maximum flow at U and f a
flow attaining it. Every vector x with max(L, f) <= x <= U has maximum flow
exactly k, because f stays feasible and no flow can exceed the value at U.
That block is assigned to level k in one step, and the rest of the box is
split into at most m disjoint boxes. One pass yields every level. The flow at
U is chosen as a min-cost maximum flow by default. Exact series-parallel
reductions are available as preprocessing.

The decomposition builds on the state-space decomposition literature for
stochastic flow networks (Doulliez 1971; Doulliez and Jamoulle 1972;
Alexopoulos 1995; Jane and Laih 2008). See [docs/REFERENCES.md](docs/REFERENCES.md).

## Install (development)

```bash
pip install -e ".[test]"
pytest
```

## AI usage

This project is developed with the help of generative AI coding assistants
(Anthropic Claude models). All code is reviewed and tested by the author, and
every result is checked against exact enumeration in the test suite.

## License

MIT
