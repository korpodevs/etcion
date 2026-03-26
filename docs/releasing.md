# Release Process

## Prerequisites

- Write access to the repository
- PyPI trusted publishing configured (see ADR-040 D3)

## Release Checklist

1. **Confirm CI is green** on the `main` branch.

2. **Update version** in `pyproject.toml`:
   ```
   version = "X.Y.Z"
   ```

3. **Update CHANGELOG.md**:
   - Rename `## [X.Y.Z] - Unreleased` to `## [X.Y.Z] - YYYY-MM-DD`
   - Add a new `## [Unreleased]` section above it

4. **Commit the version bump**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   ```

5. **Create and push the tag**:
   ```bash
   git tag vX.Y.Z
   git push origin main --tags
   ```

6. **Verify the release**:
   - Watch `.github/workflows/release.yml` in the Actions tab
   - Confirm the package appears on [PyPI](https://pypi.org/project/pyarchi/)
   - Verify: `pip install pyarchi==X.Y.Z`

## Local Build Verification (Optional)

```bash
rm -rf dist/
python -m build
twine check dist/*
```

## Hotfix Process

1. Branch from the release tag: `git checkout -b hotfix/vX.Y.Z vX.Y.Z`
2. Apply fix, update CHANGELOG, bump patch version
3. Merge to `main`, tag, push
