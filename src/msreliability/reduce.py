"""Exact series-parallel reduction of multistate edges.

Parallel edges are replaced by one edge whose capacity is the sum
(convolution of the two distributions). Two edges in series through a
non-terminal node of degree two are replaced by one edge whose capacity is
the minimum. Dangling non-terminal nodes are removed. The s-t maximum-flow
distribution is unchanged.
"""
from __future__ import annotations

import networkx as nx

__all__ = ["series_parallel_reduce"]


def _conv(p, q):
    r = [0 * p[0]] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += a * b
    return r


def _min(p, q):
    r = [0 * p[0]] * min(len(p), len(q))
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[min(i, j)] += a * b
    return r


def series_parallel_reduce(G: nx.Graph, s, t, pmf: str = "pmf") -> nx.Graph:
    """Return a reduced copy of ``G`` with the same s-t max-flow distribution.

    ``G`` may be a ``MultiGraph`` (parallel edges are merged). The result is a
    simple ``Graph``.
    """
    E = [[u, v, list(d[pmf])] for u, v, d in G.edges(data=True) if u != v]
    changed = True
    while changed:
        changed = False
        merged = {}
        for e in E:
            key = frozenset((e[0], e[1]))
            if key in merged:
                merged[key][2] = _conv(merged[key][2], e[2])
                changed = True
            else:
                merged[key] = e
        E = list(merged.values())
        degree = {}
        for u, v, _ in E:
            degree[u] = degree.get(u, 0) + 1
            degree[v] = degree.get(v, 0) + 1
        for w, deg in degree.items():
            if w in (s, t) or deg > 2:
                continue
            inc = [e for e in E if w in (e[0], e[1])]
            E = [e for e in E if w not in (e[0], e[1])]
            if deg == 2:
                x = inc[0][0] if inc[0][1] == w else inc[0][1]
                y = inc[1][0] if inc[1][1] == w else inc[1][1]
                if x != y:
                    E.append([x, y, _min(inc[0][2], inc[1][2])])
            changed = True
            break
    H = nx.Graph()
    H.add_nodes_from([s, t])
    for u, v, p in E:
        H.add_edge(u, v, **{pmf: p})
    return H
