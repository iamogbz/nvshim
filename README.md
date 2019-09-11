# NVM Shim

![LOGO](./assets/images/logo.svg)

Automagically use the correct version of node with [`nvm exec`](https://github.com/nvm-sh/nvm#usage) functionality.

![Build Status](https://github.com/iamogbz/nvshim/workflows/Build%20Python%20App/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/iamogbz/nvshim/badge.svg?branch=HEAD)](https://coveralls.io/github/iamogbz/nvshim?branch=HEAD)

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

<details>
<summary>Or you can manually build and run the installer</summary>

#### Install project dependencies

```sh
make install
```

#### Build distributable binaries

```sh
make build
```

#### Install shim and configure shell

```sh
env NVSHIM_DIR=~/.nvshim PROFILE=~/.bash_profile dist/installer
```

Or to configure multiple shell profiles simultaenously

```sh
dist/installer ~/.nvshim ~/.bash_profile ~/.config/fish/config.fish
```

</details>

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
