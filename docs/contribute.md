## Contribute

This project uses uv for dependency management and packaging.

1. Install uv from https://docs.astral.sh/

2. Fork this project into your account

3. Clone the repository to you preferred location:
```shell
$ git clone https://github.com/<user>/djangocms-xliff/
```

4. Change into the directory:
```shell
$ cd djangocms-xliff/
```

5. Create a feature branch:
```shell
$ git checkout -b feature/<branch_name>
```

6. Install the dependencies:
```shell
$ uv sync
```

8. Install [pre-commit](https://pre-commit.com/) for linting, security, formatting, etc. (only needed once):
```shell
$ uv run pre-commit install
```

9. This project uses [tox](https://tox.wiki/en/latest/) to run against all supported python, django and django-cms versions.
If you are missing a python interpreter install it on your system (or preferably use [pyenv](https://github.com/pyenv/pyenv)).
Then make sure all tests run successfully:

```shell
$ uv run tox
```

10. Optionally if you need to generate translations use the following commands:

```shell
# Generate .po files to translate in a language
uv run django-admin makemessages --locale <language_code>

# Compile .po into .mo
uv run django-admin compilemessages --ignore .tox --ignore .venv
```

11. Create the pull request
