"""Exact distribution of the s-t maximum flow in a multistate flow network.

Each undirected edge carries an independent random capacity with values
0, 1, ..., K_e and probabilities ``pmf[k]``. The functions below return the
full distribution ``Pr(F = d)`` for every level ``d`` in one pass.

Decomposition rule
------------------
Take a box of capacity vectors ``[L, U]``. Let ``k`` be the maximum flow at
``U`` and ``f`` a flow attaining it. For every ``x`` with
``max(L, f) <= x <= U`` the flow ``f`` stays feasible and no flow exceeds
``k``, so the maximum flow equals ``k`` on that whole block. The block is
assigned to level ``k`` and the rest of ``[L, U]`` is split into at most
``m`` disjoint boxes, which are processed the same way.
"""
from __future__ import annotations

import itertools
from typing import Dict, Hashable, List, Sequence, Tuple

import networkx as nx

__all__ = ["capacity_distribution", "reliability", "brute_force_distribution"]


def _edges_and_pmfs(G: nx.Graph, pmf: str):
    if G.is_directed() or G.is_multigraph():
        raise nx.NetworkXNotImplemented("only simple undirected graphs are supported")
    edges = [(u, v) for u, v in G.edges() if u != v]
    P = [list(G.edges[u, v][pmf]) for u, v in edges]
    for (u, v), p in zip(edges, P):
        if any(q < 0 for q in p) or abs(sum(p) - 1) > 1e-9:
            raise ValueError(f"edge {(u, v)}: '{pmf}' must be a probability vector")
    return list(G.nodes()), edges, P


def _max_flow(nodes, edges, x, s, t, mincost):
    """Max flow for undirected capacities x. Returns (value, |flow| per edge)."""
    D = nx.DiGraph()
    D.add_nodes_from(nodes)
    for (u, v), c in zip(edges, x):
        if c > 0:
            for a, b in ((u, v), (v, u)):
                if D.has_edge(a, b):
                    D[a][b]["capacity"] += c
                else:
                    D.add_edge(a, b, capacity=c, weight=1)
    if mincost:
        F = nx.max_flow_min_cost(D, s, t)
        value = sum(F[s].values()) - sum(F[w][s] for w in D.predecessors(s))
    else:
        value, F = nx.maximum_flow(D, s, t)
    flow = []
    for (u, v), c in zip(edges, x):
        if c > 0:
            flow.append(abs(F[u].get(v, 0) - F[v].get(u, 0)))
        else:
            flow.append(0)
    return value, flow


def _prod(values):
    r = 1
    for a in values:
        r *= a
    return r


def capacity_distribution(
    G: nx.Graph,
    s: Hashable,
    t: Hashable,
    pmf: str = "pmf",
    flow: str = "mincost",
    return_stats: bool = False,
):
    """Exact distribution of the s-t maximum flow.

    Parameters
    ----------
    G : networkx.Graph
        Undirected graph. Edge attribute ``pmf`` holds the capacity
        distribution of the edge: ``pmf[k] = Pr(capacity = k)``.
    s, t : nodes
        Source and sink.
    pmf : str
        Name of the edge attribute.
    flow : {"mincost", "max"}
        Flow chosen at the top corner of each box. ``"mincost"`` uses a
        min-cost maximum flow, which usually gives larger blocks.
    return_stats : bool
        Also return the number of max-flow evaluations.

    Returns
    -------
    dict
        ``{d: Pr(F = d)}`` for every reachable level ``d``. Probabilities are
        exact up to floating point; pass ``fractions.Fraction`` values for
        exact rational results.
    """
    if s not in G or t not in G:
        raise nx.NodeNotFound("source or sink not in G")
    nodes, edges, P = _edges_and_pmfs(G, pmf)
    m = len(edges)
    cum = [[0] + list(itertools.accumulate(p)) for p in P]

    def mass(L, U):
        return _prod(cum[i][U[i] + 1] - cum[i][L[i]] for i in range(m))

    out: Dict[int, float] = {}
    calls = 0
    stack: List[Tuple[List[int], List[int]]] = [([0] * m, [len(p) - 1 for p in P])]
    while stack:
        L, U = stack.pop()
        k, f = _max_flow(nodes, edges, U, s, t, flow == "mincost")
        calls += 1
        if k == 0:
            out[0] = out.get(0, 0) + mass(L, U)
            continue
        lo = [max(L[i], f[i]) for i in range(m)]
        out[k] = out.get(k, 0) + mass(lo, U)
        L2 = list(L)
        for i in range(m):
            if lo[i] > L[i]:
                U2 = list(U)
                U2[i] = lo[i] - 1
                stack.append((list(L2), U2))
                L2[i] = lo[i]
    out = dict(sorted(out.items()))
    return (out, {"max_flow_calls": calls}) if return_stats else out


def reliability(G: nx.Graph, s, t, d: int, pmf: str = "pmf") -> float:
    """Pr(max flow from s to t >= d)."""
    dist = capacity_distribution(G, s, t, pmf=pmf)
    return sum(p for level, p in dist.items() if level >= d)


def brute_force_distribution(G: nx.Graph, s, t, pmf: str = "pmf"):
    """Reference result by full enumeration of all capacity vectors (small graphs only)."""
    nodes, edges, P = _edges_and_pmfs(G, pmf)
    out: Dict[int, float] = {}
    for x in itertools.product(*[range(len(p)) for p in P]):
        pr = _prod(P[i][k] for i, k in enumerate(x))
        v, _ = _max_flow(nodes, edges, x, s, t, False)
        out[v] = out.get(v, 0) + pr
    return dict(sorted(out.items()))
