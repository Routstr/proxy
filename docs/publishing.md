## Publishing Docs (GitHub Pages)

1. Ensure docs build locally:

```bash
make docs-build
```

2. Set up GitHub Pages in your repository settings to serve from `gh-pages` or `/docs`.

3. Example GitHub Actions workflow (snippet):

```yaml
name: docs
on:
  push:
    branches: [ main ]
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run mkdocs build --clean
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

Alternatively, deploy to any static hosting by serving the generated `site/` directory.
