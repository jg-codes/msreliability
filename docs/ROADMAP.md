# Roadmap

1. **Reference implementation (Python).** Exact one-pass decomposition, series-parallel reduction, brute-force reference, CI. *(this release)*
2. **Compiled core.** C++ max flow and decomposition with Python bindings; identical results to the Python reference on all test networks.
3. **Benchmark harness.** Scripted, fixed-seed tables: published benchmark networks, grid and telecom topologies (SNDlib), an inland-waterway network; comparison with full enumeration, per-level decomposition and other open implementations; exactness checked in CI.
4. **Reference values.** Exact r(d) tables for the benchmark networks, released as a citable dataset.
5. **Documentation and release.** API docs, PyPI wheels, Zenodo DOI.
