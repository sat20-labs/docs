
```shell
pip install mkdocs
mkdocs new docs && cd docs || exit

pip install mkdocs-gitbook
pip install 'mkdocstrings[crystal,python]'
mkdocs serve

mkdocs build && cd site && python -m http.server

mkdocs gh-deploy

```