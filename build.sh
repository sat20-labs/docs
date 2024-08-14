#!/bin/bash
# set -x
# set -e

mkdocs build -f zh/mkdocs.yml
mv zh/site ./

mkdocs build -f en/mkdocs.yml
mkdir site/en && mv en/site/* ./site/en
