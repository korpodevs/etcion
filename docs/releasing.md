# Release Process

## Prerequisites

- Write access to the repository
- PyPI trusted publishing configured (see ADR-040 D3)

## Release Checklist

1. **Confirm CI is green** on the `develop` branch.

2. **Update version** in `pyproject.toml`:
   ```
   version = "X.Y.Z"
   ```

3. **Update CHANGELOG.md**:
   - Add a new `## [X.Y.Z] - YYYY-MM-DD` section with release notes
   - Move items from any `## [Unreleased]` section into the new version

4. **Update version assertions** in `test/test_packaging.py` and `test/test_scaffold.py`.

5. **Commit and push to develop**:
   ```bash
   git add pyproject.toml CHANGELOG.md test/test_packaging.py test/test_scaffold.py
   git commit -m "Release vX.Y.Z"
   git push origin develop
   ```

6. **Create a PR from develop to main**:
   ```bash
   gh pr create --base main --head develop \
     --title "Release vX.Y.Z" \
     --body "## Summary
   <changelog excerpt>

   ## Closes
   Closes #N, closes #N, ...
   "
   ```
   - Wait for CI to pass on the PR
   - Review the diff as a final sanity check

7. **Merge the PR** (merge commit, not squash):
   ```bash
   gh pr merge --merge
   ```

8. **Tag and push**:
   ```bash
   git checkout main
   git pull origin main
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   This triggers `.github/workflows/release.yml` which builds and publishes to PyPI.

9. **Create a GitHub Release**:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z: <title>" --notes "See CHANGELOG.md for details."
   ```

10. **Return to develop**:
    ```bash
    git checkout develop
    git merge main   # pick up the merge commit
    git push origin develop
    ```

11. **Verify the release**:
    - Watch the Actions tab for the release workflow
    - Confirm the package on [PyPI](https://pypi.org/project/etcion/)
    - `pip install etcion==X.Y.Z`

## Local Build Verification (Optional)

```bash
rm -rf dist/
python -m build
twine check dist/*
```

## Hotfix Process

1. Branch from the release tag: `git checkout -b hotfix/vX.Y.Z vX.Y.Z`
2. Apply fix, update CHANGELOG, bump patch version
3. Create PR to `main`, merge, tag, push
4. Merge fix back to `develop`
