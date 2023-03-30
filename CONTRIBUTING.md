# Contributing

Please, do not hesitate to contribute if you feel that this tool needs some features or improvements. The easiest way is to [create an issue](https://github.com/nullJaX/changelog-keeper/issues), either with `enhancement` or `bug` tag. Otherwise, if you want to provide more active code contribution, please fork the repository, include your changes and open a pull request to this repo. Here are some steps to do it:

1. Fork the project (by clicking the Fork button)
2. Clone the repository to your local machine (`git clone <url_to_the_forked_repository>`)
3. Once you enter project directory, create your feature branch (`git checkout -b feature/my_feature`)
4. Follow the [development installation steps](#development-installation)
5. Write the code (ideally with the tests evaluating the changes)
6. Check your changes by running commands from the [development usage section](#development-usage)
7. Commit your changes (`git commit -am 'Add a_feature'`)
8. Push changes to the branch (`git push origin feature/my_feature`)
9. Open a pull request

## Development installation

```bash
# After cloning the repository, enter project directory
cd changelog_keeper/

# Create a virtual environment
python -m virtualenv .venv/

# Open a virtual environment, to exit environment use `deactivate` command
source .venv/bin/activate

# Install development requirements
pip install -r requirements_dev.txt

# Install package in development mode (executed from the source code)
python setup.py develop
```

## Development usage

Please make sure that you first installed everything that was described in the [development installation steps](#development-installation), including the virtual environment. This will enable you to run the tool **from the source code** and not pre-built package. Following commands will help you test your changes and format them correctly according to the Python standards:

```bash
# Running the tests with coverage
pytest

# Lint the code using ruff
ruff .
# Alternatively with pylint
pylint changelog_keeper

# Format the code using black
black changelog_keeper
```