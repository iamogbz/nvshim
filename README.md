# NVM Shim

![LOGO](https://i.ibb.co/PZTm9Sr/logo.png)

Automagically use the correct version of node with [`nvm exec`](https://github.com/nvm-sh/nvm#usage) functionality.

![Build Status](https://github.com/iamogbz/nvshim/workflows/Build%20Python%20App/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/iamogbz/nvshim/badge.svg?branch=HEAD)](https://coveralls.io/github/iamogbz/nvshim?branch=HEAD)
[![Pypi](https://img.shields.io/pypi/v/nvshim)](https://pypi.org/project/nvshim/)
![Stage](https://img.shields.io/pypi/status/nvshim)
![Wheel](https://img.shields.io/pypi/wheel/nvshim)

> **No more `nvm use`**

This will use existing [`.nvmrc`](https://github.com/nvm-sh/nvm#nvmrc) file, falling back to the [`nvm alias default`](https://github.com/nvm-sh/nvm#usage-1) version if no config detected.

## Installation

### Pip

```sh
pip install nvshim
```

### Build

#### Clone project repository

```sh
git clone git@github.com:iamogbz/nvshim.git
```

#### Pip install python project

```sh
pip install nvshim/
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

## Contribution

All forms of contribution welcome, please see [guide](./CONTRIBUTING.md).

```sh
make install
```

```sh
make tests
```
