# qbraid-qir

qBraid-SDK extension providing support for QIR conversions

## Local install

```bash
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install -e .
```

## Run tests

```bash
pip install -r requirements-dev.txt
pytest tests
```

with coverage report

```bash
pytest --cov=qbraid_qir --cov-report=term tests/
```

## Build docs

```bash
pip install -r docs/requirements.txt
make docs/html
```
