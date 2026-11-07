import random
from fractions import Fraction

import networkx as nx
import pytest

from msreliability import (
    brute_force_distribution,
    capacity_distribution,
    reliability,
    series_parallel_reduce,
)


def bridge():
    # Bridge network with the edge distributions of Yeh et al. (2022), Fig. 1 / Table 1
    # (arXiv 2107.13665 v1, as transcribed; not yet compared with the journal version).
    G = nx.Graph()
    pmfs = {
        (1, 2): [0.1, 0.2, 0.7],
        (1, 3): [0.05, 0.10, 0.85],
        (2, 3): [0.01, 0.19, 0.80],
        (2, 4): [0.10, 0.15, 0.75],
        (3, 4): [0.025, 0.075, 0.900],
    }
    for e, p in pmfs.items():
        G.add_edge(*e, pmf=p)
    return G


def random_graph(n, m, seed, states=5):
    rng = random.Random(seed)
    while True:
        G = nx.gnm_random_graph(n, m, seed=rng.randrange(10**9))
        if nx.is_connected(G):
            break
    for u, v in G.edges():
        w = [rng.random() for _ in range(states)]
        G.edges[u, v]["pmf"] = [x / sum(w) for x in w]
    return G


def close(a, b, tol=1e-12):
    return all(abs(a.get(k, 0) - b.get(k, 0)) <= tol for k in set(a) | set(b))


def test_bridge_level_four():
    # Flow 4 needs edges (1,2), (1,3), (2,4), (3,4) at capacity 2.
    assert reliability(bridge(), 1, 4, 4) == pytest.approx(0.7 * 0.85 * 0.75 * 0.9, abs=1e-12)


def test_bridge_matches_brute_force():
    G = bridge()
    assert close(capacity_distribution(G, 1, 4), brute_force_distribution(G, 1, 4))


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("flow", ["mincost", "max"])
def test_random_matches_brute_force(seed, flow):
    G = random_graph(5, 7, seed, states=4)
    assert close(capacity_distribution(G, 0, 4, flow=flow), brute_force_distribution(G, 0, 4))


def test_exact_fractions():
    G = nx.Graph()
    G.add_edge("s", "a", pmf=[Fraction(1, 4), Fraction(3, 4)])
    G.add_edge("a", "t", pmf=[Fraction(1, 2), Fraction(1, 2)])
    G.add_edge("s", "t", pmf=[Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)])
    dist = capacity_distribution(G, "s", "t")
    assert sum(dist.values()) == 1
    assert dist == brute_force_distribution(G, "s", "t")


@pytest.mark.parametrize("seed", range(4))
def test_reduction_preserves_distribution(seed):
    G = random_graph(6, 8, seed, states=3)
    H = series_parallel_reduce(G, 0, 5)
    assert H.number_of_edges() <= G.number_of_edges()
    assert close(capacity_distribution(H, 0, 5), brute_force_distribution(G, 0, 5))


def test_fewer_calls_than_enumeration():
    G = random_graph(6, 8, 1, states=5)
    _, stats = capacity_distribution(G, 0, 5, return_stats=True)
    assert stats["max_flow_calls"] < 5 ** 8
