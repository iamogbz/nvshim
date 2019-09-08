# NVM Shim

![LOGO](./assets/images/logo.svg)

Automagically use the correct version of node with [`nvm exec`](https://github.com/nvm-sh/nvm#usage) functionality.

![Build Status](https://github.com/iamogbz/nvshim/workflows/Build%20Python%20App/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/iamogbz/nvshim/badge.svg)](https://coveralls.io/github/iamogbz/nvshim)

> **No more `nvm use`**

This will use existing [`.nvmrc`](https://github.com/nvm-sh/nvm#nvmrc) file, falling back to the [`nvm alias default`](https://github.com/nvm-sh/nvm#usage-1) version if no config detected.

## Installation

### Script

```sh
curl -s https://github.com/iamogbz/nvmshim/releases/download/v0.0.1/installer.py | python
```

### Manual

#### Download distributable

Get specific version from the [releases page](https://github.com/iamogbz/nvmshim/releases).

#### Extract into folder `~/.nvshim`

```sh
unzip nvmshim.zip -o ~/.nvmshim
```

- nvshim.py
- node.sh
- npm.sh

#### Ensure scripts can be run

Make files executable

```sh
chmod +x nvmshim.py
chmod +x node.py
chmod +x npm.py
```

#### Add to shell scripts path

Add `~/.nvshim` to `PATH`

```sh
export PATH="~/.nvshim:$PATH"
```

#### Profit

## Configuration

Reads all configuration from the environment.

### [`NVM_DIR`](https://github.com/nvm-sh/nvm#installation-and-update)

Relies on nvm being installed and configured correctly.

### `NVSHIM_AUTO_INSTALL`

Set to `1` or `true` to auto install specified version of node if not installed by `nvm`.

### `NVSHIM_VERBOSE`

Set to `1` or `true` to show more information on the shimmed node process.

Otherwise set to `0` or `false` or nothing.

## Contribution

All forms of contribution welcome, please see [guide](./CONTRIBUTING.md).
