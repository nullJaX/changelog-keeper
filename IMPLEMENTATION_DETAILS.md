# Implementation details

## Changelog Keeper and keep-a-changelog convention

Changelog Keeper mostly follows the same principles as [keep-a-changelog](https://keepachangelog.com/), however some adjustments have been made in order to make this tool more automation friendly.

### Version Links

Version links are not referenced at the bottom of the file. Instead, the link is attached to the version name (`[VERSION_NAME](URL)`). The name in the version heading is then displayed as a link to specified URL. If the reference/URL is not provided when the version is being released, no URL is added and the version name will be displayed as `[VERSION_NAME]`.

This design decision was mainly made to keep implementation easy and the biggest disadvantage of this solution is readability when the file is opened in a text editor. However, this tool aims to reduce the number of manual changes to the file and tries to handle the changelog on its own.

### Unreleased entries prefix

Changelog entries that are made under an unreleased version contain a prefix `<VERSION_NAME-CHANGE_TYPE/>` (ie. `<Unreleased-Removed/>`) in each line. This prefix is detected every time the tool opens a file and sorts these entries to appropriate version and change type. They are automatically removed when the version state changes to `RELEASED` or `YANKED`. Here are some examples of valid entries:

```Markdown
- <Unreleased-Added/>Single line example

- <Unreleased-Fixed/>Multi line
  <Unreleased-Fixed/>example
```

However, it might also happen that these entries are scrambled. In this case, the tool will print at its standard output that the operation could not be performed and manual intervention is necessary. Here are some invalid entries that will fail the execution:

```Markdown
- <Unreleased-Added/>Multi line
  example

- Another multi line
  <Unreleased-Changed/>example

- <Unreleased-Security/>Yet another
  <OtherVersion-Security/>invalid example

- <Unreleased-Deprecated/>And another
  <Unreleased-Fixed/>example

- <NonExistingVersion-Fixed/>Entry for non-existing version

- <Unreleased-NonExistingChangeType/>Entry for non-existing change type
```

This solution was introduced to cover cases where the repository merge or rebase happened and changes in the file were not recognized by VCS as conflicts.

## CI/CD integration notes

### Version links

Version links are treated as raw strings and are not validated. This was left intentionally for the user to determine the URL scheme based on the workflow, the repository hosting platform (Bitbucket/GitHub/Gitlab/etc.) and version control system. [Keep-a-changelog](https://keepachangelog.com/) standard proposes following scheme for GitHub based repositories:

- For the first released version: `https://github.com/<user>/<project>/releases/tag/<version_tag>`
- For next released versions: `https://github.com/<user>/<project>/compare/<old_version_tag>...<new_version_tag>`
- For the Unreleased version: `https://github.com/<user>/<project>/compare/<latest_version_tag>...HEAD`

For the same reason, currently there is no support for setting up the URL for the Unreleased version. If you want to automatically release changelog versions in your CI/CD setup (and your repository is Git based), please investigate `git rev-list` and `git describe` commands to obtain latest tag names.

### File validation

In addition to the [version changes validation](#unreleased-entries-prefix), Changelog Keeper also performs following checks:

1. The number of unreleased versions has to be equal to 1
2. The unreleased version (identified by `Unreleased` name) has to be the first version in the file (at the top)

In case of the validation failure, the tool prints the error message in the standard output and returns non-zero exit code.
However, the validation will not fail if any formatting fixes were applied, more specifically:

- entries have been sorted during the process
- the file was improperly formatted (ie. one line separation missing between Markdown sections)

If the changelog check is required as a CI/CD quality gate, this behavior should be implemented to cover mentioned cases, for example by executing `git status --short` or `git diff --name-only` and checking whether the changelog file is listed in the result.