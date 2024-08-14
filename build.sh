#!/bin/bash
# set -x
# set -e

mkdocs build -f ./zh/mkdocs.yml
rm -rf ./site && mv ./zh/site ./

if [ ! -d "./site/en" ]; then
    mkdir -p ./site/en
fi

mkdocs build -f ./en/mkdocs.yml
mv en/site/* ./site/en

rm -rf en/site
