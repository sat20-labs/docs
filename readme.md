
# install env
```shell
pip install mkdocs
# mkdocs new docs && cd docs || exit
# pip install mkdocs-gitbook
# pip install 'mkdocstrings[crystal,python]'

# mkdocs serve
# mkdocs build && cd site && python -m http.server
# mkdocs gh-deploy
```

# build docs
```shell
./build.sh
```

# test docs site with local http server
```shell
./build.sh
python -m http.server
```