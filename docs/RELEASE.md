# Release runbook — generic-graphql-mcp

How to cut a release of `generic-graphql-mcp` to PyPI. Publishing uses **GitHub
Actions OIDC Trusted Publishing** — there is no long-lived PyPI token in CI.

## Version source of truth

The distribution version is taken from **`native/Cargo.toml`** (`[package]
version`) by maturin (`pyproject.toml` declares `dynamic = ["version"]`). Keep
it in sync with the git tag you push — the tag and the built artifact version
MUST match (REL-02).

```
native/Cargo.toml  →  version = "X.Y.Z"
git tag            →  vX.Y.Z
```

## One-time PyPI setup (Trusted Publisher)

The project must have a **pending publisher** (or an existing project with a
trusted publisher) registered on PyPI, or the publish job fails with
`invalid-publisher`. Register at:

- New project: https://pypi.org/manage/account/publishing/ → **Add a pending publisher**
- Existing project: `https://pypi.org/manage/project/generic-graphql-mcp/settings/publishing/`

Claims (must match `.github/workflows/publish.yml` exactly):

| Field              | Value                    |
|--------------------|--------------------------|
| PyPI Project Name  | `generic-graphql-mcp`    |
| Owner              | `mshegolev`              |
| Repository name    | `graphql-mcp`            |
| Workflow name      | `publish.yml`            |
| Environment name   | `pypi`                   |

> Repository name is `graphql-mcp` (the GitHub repo was not renamed even though
> the distribution was). If the repo is ever renamed, update this claim.

## Cutting a release

1. Ensure `main` is green (CI: lint-and-test + wheels + sdist).
2. Bump the version in `native/Cargo.toml` to `X.Y.Z` and update `CHANGELOG.md`.
   Commit: `chore(release): X.Y.Z`.
3. Tag and push:

   ```sh
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin main
   git push origin vX.Y.Z
   ```

   The pushed tag triggers `.github/workflows/publish.yml` (build wheels + sdist,
   then OIDC publish to PyPI).

4. Watch the run:

   ```sh
   gh run list --repo mshegolev/graphql-mcp --workflow "Publish to PyPI" --limit 1
   ```

   (If your shell exports an invalid `GITHUB_TOKEN`, prefix with
   `env -u GITHUB_TOKEN` so `gh` uses the keychain login.)

## Rerun on failure

Wheels build fine but the final `publish` step failed (e.g. you fixed the
pending publisher afterwards)? Re-run only the failed job — no new tag needed:

```sh
env -u GITHUB_TOKEN gh run rerun <run-id> --repo mshegolev/graphql-mcp --failed
```

If the failure was `invalid-publisher`, fix the Trusted Publisher claims above
first, then rerun.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `invalid-publisher: ... no corresponding publisher` | No/mismatched Trusted Publisher on PyPI | Register the pending publisher with the exact claims above, then rerun the failed publish job |
| Wheel version ≠ tag | `native/Cargo.toml` not bumped | Sync `native/Cargo.toml` to the tag, re-tag |
| `File already exists` on PyPI | Version already published | Bump to a new version; PyPI versions are immutable |
