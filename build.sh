#!/bin/bash
# set -x
# set -e

# Remove all directories except 'src'
find . -maxdepth 1 -type d ! -name '.' ! -name 'src' ! -name '.*' -exec rm -rf {} +

# Remove all files except 'CNAME', 'README.md', and 'bash.sh'
find . -maxdepth 1 -type f ! -name 'CNAME' ! -name 'README.md' ! -name 'build.sh' ! -name '.*' -exec rm -f {} +

mkdocs build -f ./src/zh/mkdocs.yml
mv ./src/zh/site/* ./
rm -rf ./src/zh/site

if [ ! -d "./en" ]; then
    mkdir -p ./en
fi

mkdocs build -f ./src/en/mkdocs.yml
mv ./src/en/site/* ./en
rm -rf ./src/en/site
