# Reviews Parsing MLSys

Set up a new repo with Poetry.

# How to start

Install these prerequisites:
- Virtual environment with Python 3.9. You can choose to install Miniconda to choose which Python version to create a new virtual env with.
- Poetry >= 1.8.3. Make sure Poetry use the correct Python executable from the above venv by running `poetry env info`.

## Install packages

```
# Create a new Pytohon 3.9 environment
# Example conda environment at current dir
conda create --prefix ./.venv python=3.9
poetry env use ./.venv/bin/python

# This command will automatically install all packages specified in `poetry.lock` file.
poetry install
```
