# Release guide

This guide is for maintainers publishing a new version of [Matrix Crypto](https://pypi.org/project/matrixcrypto/). PyPI releases are immutable: changes to code or the PyPI description require a new version.

## Prepare the release

1. Update the version in `pyproject.toml` and `src/matrixcrypto/__init__.py`.
2. Review the bundled lists in `src/matrixcrypto/data/` and refresh them if needed.
3. Run the tests and build a wheel and source archive with Python 3.12 or newer.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade build twine
python -m pip install -e .
python -m unittest discover -s tests
rm -rf dist
python -m build
python -m twine check dist/*
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\activate`. Remove the previous `dist` directory before building so only the new version's files are uploaded.

Inspect the `.whl` and `.tar.gz` files in `dist/`. Install the wheel in a fresh virtual environment, then check `matrixcrypto --help` and `matrixcrypto-offline --help`. Test the display in a color terminal.

## Publish

Commit and push the release source before uploading so the GitHub links on PyPI match the release. A Git tag such as `v0.1.1` can identify the commit used to build the archives.

For a manual upload, use a project-scoped PyPI API token. Keep it out of the repository and shell history. Twine's username for an API token is `__token__`; it prompts privately for the full token, including the `pypi-` prefix.

```bash
python -m twine upload --username __token__ dist/*
```

After upload, check the [PyPI project page](https://pypi.org/project/matrixcrypto/) and install the new version from PyPI in a clean environment. `pip install matrixcrypto` installs the latest available release; `pip install matrixcrypto==0.1.0` is an example that selects one specific release.

For automated releases, PyPI [Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/) can replace stored API tokens.
