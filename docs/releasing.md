# Release checklist

The distribution name selected for this project is `nyaaapi-client`. At the time of the 0.1.0 packaging check, PyPI's JSON API returned HTTP 404 for that project name. PyPI names are first-come, first-served, so check again immediately before an upload: <https://pypi.org/pypi/nyaaapi-client/json>.

## Build and verify locally

From the repository root:

```console
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest -q
python -m build
python -m twine check dist/*
```

Inspect the wheel metadata and install the wheel in a clean environment before release. Do not upload a second build with the same version; increment `project.version` and create a new tag for any corrections.

## TestPyPI

Create a TestPyPI account and API token, then upload the verified distributions:

```console
python -m twine upload --repository testpypi dist/*
```

Twine prompts for credentials. Use `__token__` as the username and the TestPyPI token as the password. Install from TestPyPI with `--index-url https://test.pypi.org/simple/` (and `--extra-index-url https://pypi.org/simple/` for runtime dependencies, which may not be present on TestPyPI).

## PyPI and GitHub release

After validating the TestPyPI install, create the final Git tag and publish the GitHub release from that tag. Upload the exact same distributions to PyPI:

```console
python -m twine upload dist/*
```

The project must be pushed to a GitHub repository before a GitHub release can be published. Trusted publishing also requires configuring the repository owner, repository name, workflow filename, and PyPI project on the respective services; this repository currently has no remote configured.
