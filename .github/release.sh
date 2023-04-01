#!/usr/bin/env bash
set -e
echo "---- INSTALL ----"
git checkout master
git pull
source .venv/bin/activate
pip install -r requirements_dev.txt
python setup.py develop
echo "--- CHECK TAG ---"
VERSION=$(python -c "from changelog_keeper import VERSION;print(VERSION)")
echo "Detected current version:" $VERSION
for tag in $(git tag); do
    if [[ "$VERSION" == "$tag" ]]; then
        echo "ERROR: Version $VERSION is already present in the repo."
        exit 1
    fi
done
echo "--- LINT/TEST ---"
ruff .
pytest
echo "- BUILD/PUBLISH -"
python -m build
python -m twine upload dist/*
echo "------ TAG ------"
git tag $VERSION
git push origin $VERSION
