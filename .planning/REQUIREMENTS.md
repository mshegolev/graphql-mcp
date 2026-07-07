# generic-graphql-mcp v2.3 — Requirements

**Milestone:** v2.3 Release & Staging Enablement
**Scope:** PyPI publish via OIDC Trusted Publishing, local deployment wired to EORD staging with ISSO auth, and CI hardening (dependency + async config fixes).
**Predecessor:** v2.2 Performance Excellence (completed 2026-06-18, phases 17-19)

---

## Requirements

### Release (PyPI)

- [ ] **REL-01**: A maintainer publishes `generic-graphql-mcp` to PyPI by pushing a release tag; the GitHub Actions "Publish to PyPI" workflow completes green via OIDC Trusted Publishing with no `invalid-publisher` — verified by a successful publish run and the version appearing on pypi.org.
- [ ] **REL-02**: The published distribution version equals the release tag (`native/Cargo.toml` is the single version source, synced to the tag) — verified by the uploaded artifact version matching the pushed tag.
- [ ] **REL-03**: A release runbook documents the pending-publisher claims (project, owner, repo, workflow, environment) and the rerun-on-failure command, so releases are reproducible without tribal knowledge — verified by the runbook existing in-repo (e.g. `docs/RELEASE.md`).

### Staging Enablement

- [ ] **STG-01**: An operator runs the MCP server locally in both `serve` (HTTP) and `stdio` modes pointed at the EORD staging federation gateway via a single documented launcher — verified by the server starting and `/ready` returning 200 (serve) against staging.
- [ ] **STG-02**: The server obtains a live bearer token from ISSO (Keycloak) via password-grant at startup (`client_id=eordui-stage`, `username=sa0000eord`); no placeholder or hardcoded token is committed — verified by a successful authenticated introspection against staging.
- [ ] **STG-03**: Staging connection config (endpoint, proxy bypass, SSL verification) is derived reproducibly from `integration-tests/pytest.ini`, with credentials supplied via environment/secret store only — verified by launching from a clean checkout with only credentials in env.
- [ ] **STG-04**: A staging smoke check confirms live connectivity — `introspect` returns Query fields and `list_subgraphs` returns federation subgraphs — verified by the smoke script exiting 0 against staging.

### CI Hardening

- [ ] **CIH-01**: `pip install .[dev]` resolves successfully — the nonexistent `pytest-syrupy` dependency is corrected to `syrupy` — verified by a clean dev install completing in CI.
- [ ] **CIH-02**: Async tests are collected and pass — the pytest config section header is corrected so `asyncio_mode=auto` applies — verified by the full suite running with zero "async def not natively supported" errors.
- [ ] **CIH-03**: The CI `lint-and-test` workflow is green on `main` across the Python version matrix — verified by a passing CI run.

---

## Future Requirements (deferred)

- **REG-01**: Publish the server to the MCP registry (`server.json` / glama.json) so it is discoverable by MCP clients.
- **REPO-01**: Rename the GitHub repository `mshegolev/graphql-mcp` → `generic-graphql-mcp` and update the trusted-publisher claim accordingly.
- **PROD-01**: Production (non-staging) deployment target with production auth.
- **ENV-01**: Automate developer-machine `GITHUB_TOKEN` hygiene (a stale env token overrides the valid keychain token).

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| GitHub repo rename | Separate manual GitHub action; trusted publisher is keyed on the current repo name `graphql-mcp`, so publishing works without it. Deferred to REPO-01. |
| MCP registry publish | Orthogonal to PyPI distribution; deferred to REG-01. |
| Production deployment | This milestone targets staging only. |
| Re-running v1.0–v2.2 phases | Those milestones shipped; v2.3 is net-new scope. |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CIH-01 | Phase 20 | Pending |
| CIH-02 | Phase 20 | Pending |
| CIH-03 | Phase 20 | Pending |
| REL-01 | Phase 21 | Pending |
| REL-02 | Phase 21 | Pending |
| REL-03 | Phase 21 | Pending |
| STG-01 | Phase 22 | Pending |
| STG-02 | Phase 22 | Pending |
| STG-03 | Phase 22 | Pending |
| STG-04 | Phase 22 | Pending |
