# Contributing

Install the development environment:

```bash
python -m pip install -e ".[dev]"
```

Before opening a pull request, run:

```bash
pytest
ruff check src tests
recurspec contract check docs/architecture
recurspec structure check .
recurspec stack check .
recurspec reconcile plan .
python -m build
```

Use the canonical terms in [CONTEXT.md](./CONTEXT.md). Put incomplete product work only in
[ROADMAP.md](./ROADMAP.md). New behavior needs an interface-level test, and research
claims need a primary source in [docs/research/foundations.md](./docs/research/foundations.md).

Do not include local evidence logs, credentials, consumer-project source, or generated
build artifacts.
