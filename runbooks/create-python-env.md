# Create a Python environment

## Create and activate a python environment

Note: The environment with the versions defined in requirements.txt and requirements-awscli.txt has been tested with python 3.10 and 3.11

* Make sure you deactivate any virtual environment in your terminal, eg: `conda deactivate`. After deactivating you SHOULDN'T see any environment name in parentheses at the beginning of your terminal, eg:

```shellsession
(base) rami001@CCFFH az-cruk-crispr-guide-count %
```

[Create](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) the environment:

```shellsession
python3 -m venv python/env
```

[Activate](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#activating-a-virtual-environment) a python environment:

```shellsession
source python/env/bin/activate
```

## Using requirements files

Install packages using a [requirements file](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#using-requirements-files):

```shellsession
python3 -m pip install -r python/requirements.txt -r python/requirements-dev.txt
```

* Check the dependencies in the newly created environment:

```shellsession
source python/env/bin/activate
pip freeze
``````

## Deactivate the venv environment

* To deactivate your `venv` environment run:

```shellsession
deactivate
```
