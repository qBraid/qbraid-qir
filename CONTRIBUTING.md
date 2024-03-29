# Contributing

Welcome! We're delighted that you're interested in contributing. Your help is essential for keeping the project great.

## Getting Started

Before you start working on a new feature or a fix, here's how you can contribute:

1. **Fork the repository**: Visit the GitHub page of our project and use the "Fork" button to create a copy of the project in your own GitHub account.
2. **Create a Development Branch**: After forking, clone the repository to your local machine and create a new branch for your development. Use a descriptive name for your branch, such as `feature-<feature-name>` or `bugfix-<bug-description>`.
3. **Commit Your Changes**: Make your changes in your development branch and commit them. Be sure to write clear, concise commit messages.
4. **Push to Your Fork**: Push your changes to your forked repository on GitHub.
5. **Create a Pull Request**: Go to the original project repository and click on "Pull Requests", then click the "New Pull Request" button

### Development install

```shell
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install -e '.[cirq,qasm3]'
```

## Pull request checklist

### Run tests

Workflow: [`main.yml`](.github/workflows/main.yml)

- [ ] All unit tests are passing
- [ ] New/modified code has corresponding unit tests and satisfies ``codecov`` checks.

Install pytest:

```shell
pip install qbraid pytest pytest-cov
```

Run unit tests:

```shell
pytest tests
```

Generate a coverage report and verify that project and diff ``codecov`` are both upheld:

```bash
pytest --cov=qbraid_qir --cov-report=term tests/
```

### Build docs

Workflow: [`docs.yml`](.github/workflows/docs.yml)

- [ ] Docs builds are passing
- [ ] New/modified code has appropriate docstrings
- [ ] Tree stubs are updated, if applicable
- [ ] Examples on how to use new/updated features added to User Guide

Static docs pages (e.g. User Guide) are written using reStructuredText (reST), which is the default plaintext markup language used by [Sphinx](https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html). It's pretty straightforward once you get the hang of it. If you're unfamiliar, [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#restructuredtext-primer) is a good place to start.

Use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
to specify attributes, arguments, exceptions, returns, and other related info. The docstrings are compiled into HTML using Sphinx, so to add relative links, in-line markup, bulleted lists, code-blocks, or do other types of formatting inside of docstrings, use the `reST` syntax mentioned (linked) above.

Install sphinx and other docs requirements:

```shell
pip install -e '.[docs]'
```

Then, build docs with:

```shell
cd docs
make html
```

View docs in local browser window:

```shell
open build/html/index.html
```

### Code style

Workflow: [`format.yml`](.github/workflows/format.yml)

- [ ] Formatting/linters checks pass
- [ ] All files have appropriate licensing header

For code style, our project uses a combination of [isort](https://github.com/PyCQA/isort), [pylint](https://github.com/pylint-dev/pylint),
and [black](https://github.com/psf/black). Specific configurations for these tools should be added to [`pyproject.toml`](pyproject.toml).

Install linters:

```shell
pip install 'black[jupyter]' isort pylint
```

Run the following and make changes as needed to satisfy format checks:

```shell
black qbraid_qir tests examples
isort qbraid_qir tests
pylint qbraid_qir tests
```

Add licensing headers to all files:

```shell
python3 tools/verify_headers.py --fix
```
