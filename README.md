# NVM Shim

![LOGO](https://i.ibb.co/PZTm9Sr/logo.png)

Automagically use the correct version of node with [`nvm exec`](https://github.com/nvm-sh/nvm#usage) functionality.

![Build Status](https://github.com/iamogbz/nvshim/workflows/Python%20App/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/iamogbz/nvshim/badge.svg?branch=master)](https://coveralls.io/github/iamogbz/nvshim?branch=master)
[![Pypi](https://img.shields.io/pypi/v/nvshim)](https://pypi.org/project/nvshim/)
![Stage](https://img.shields.io/pypi/status/nvshim)
![Wheel](https://img.shields.io/pypi/wheel/nvshim)
[![Dependabot badge](https://badgen.net/github/dependabot/iamogbz/nvshim/?icon=dependabot)](https://app.dependabot.com)

> **No more `nvm use`**

This will use existing [`.nvmrc`](https://github.com/nvm-sh/nvm#nvmrc) file, falling back to the [`nvm alias default`](https://github.com/nvm-sh/nvm#usage-1) version if no config detected.

## Installation

### Pip

```sh
pip install nvshim
```

### Github

```sh
pip install git+git://github.com/iamogbz/nvshim.git
```

## Configuration

Reads all configuration from the environment.

### [`NVM_DIR`](https://github.com/nvm-sh/nvm#installation-and-update)

Relies on nvm being installed and configured correctly.

### `NVSHIM_AUTO_INSTALL`

Set to `1` or `true` to auto install specified version of node if not installed by `nvm`.

### `NVSHIM_VERBOSE`

Set to `1` or `true` to show more information on the shimmed node process.

Otherwise set to `0` or `false` or nothing.

## Caveats

To allow the `nvshim` installed `node` shim work in all directories, you'll need to stop sourcing `nvm.sh` in your shell rc i.e. `bash_profile`, `zshrc` etc. 

Just comment out the `source /Users/me/.nvm/nvm.sh` in your shell startup script. This is optional and prevents `nvm` from taking control of your shell path on launch.

## Contribution

All forms of contribution welcome, please see [guide](./CONTRIBUTING.md).

```sh
make install
```

```sh
make tests
```
