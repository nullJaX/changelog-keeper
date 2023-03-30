# Changelog Keeper

*Command line utility for keeping your changelog tidy*

## About the project

This tool aims to:

1. make your changelog file standardized; and
2. reduce the time spent on updating the changelog file by providing a suite of basic commands.

The Changelog standard is based on the [keep-a-changelog](https://keepachangelog.com/) convention with few adjustments, described in [this document](IMPLEMENTATION_DETAILS.md#changelog-keeper-and-keep-a-changelog-convention).

It is also possible (with some additional scripting/tooling) to incorporate this utility into your *Continuous Integration & Continuous Delivery* routines. There are few things to consider, mentioned in [this document](IMPLEMENTATION_DETAILS.md#cicd-integration-notes).

## Getting started

### Prerequisites

* Python >= 3.7
* Pip

### Installation

```bash
# general installation
pip install changelog-keeper

# with specific version
pip install changelog-keeper==1.0.0
```

## Usage

Changelog Keeper provides five simple commands allowing basic operations on the changelog file:

```bash
# Create new, empty changelog file
clkpr create [-f PATH]

# Add new entry to the changelog file
clkpr add [-f PATH] CHANGE_TYPE ENTRY

# Validate and (if needed and possible) fix the changelog file
clkpr check [-f PATH]

# Release a version (with optional link)
clkpr release [-f PATH] [-r URL] VERSION_NAME

# Yank released version
clkpr yank [-f PATH] VERSION_NAME

# For more details, one can check the help messages for the tool: `clkpr -h`
# and for a particular command: `clkpr <command> -h`
```

## Contributing

Please have a look into [CONTRIBUTING](CONTRIBUTING.md) file for detailed suggestions regarding project contribution.

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) file for more information.