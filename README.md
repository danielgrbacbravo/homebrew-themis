# Themis Homebrew tap

Install the [Themis CLI/TUI](https://github.com/danielgrbacbravo/themis) on macOS or Linux:

```sh
brew install danielgrbacbravo/themis/themis
themis --version
themis login
themis
```

The formula builds from a checksum-pinned source release with vendored dependencies. Go is a build dependency; Poppler is installed for PDF reading. Each machine keeps its own authentication settings. No university credentials are included.

Update with `brew update && brew upgrade themis`. Remove the package with `brew uninstall themis`; local Themis configuration is left intact.

The updater uses GitHub CLI (`gh`), included on GitHub-hosted runners. The update workflow checks the latest stable release every six hours and can also be run manually from Actions. It verifies the source archive against the release checksum before updating the formula. It uses only this repository's built-in workflow token; no personal access token is required. The formula install/test workflow can be dispatched manually after an automated update (GitHub does not trigger push workflows for commits made with its workflow token).

Direct binary downloads, checksums, and corresponding source are available on the main repository's [Releases](https://github.com/danielgrbacbravo/themis/releases) page.
