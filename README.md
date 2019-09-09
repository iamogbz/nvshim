# NVM Shim

![LOGO](./assets/images/logo.svg)

Automagically use the correct version of node with [`nvm exec`](https://github.com/nvm-sh/nvm#usage) functionality.

![Build Status](https://github.com/iamogbz/nvshim/workflows/Build%20Python%20App/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/iamogbz/nvshim/badge.svg?branch=HEAD)](https://coveralls.io/github/iamogbz/nvshim?branch=HEAD)

> **No more `nvm use`**

This will use existing [`.nvmrc`](https://github.com/nvm-sh/nvm#nvmrc) file, falling back to the [`nvm alias default`](https://github.com/nvm-sh/nvm#usage-1) version if no config detected.

## Installation

> TODO: implement readme documentation spec

### Pip

```sh
pip install nvshim
```

### Script

Use the distributed installer

```sh
curl -s https://github.com/iamogbz/nvmshim/releases/download/v0.0.1/installer.py | env NVSHIM_DIR=~/.nvm/shims PROFILE=~/.bashrc python
```

> Each installer is keyed to its release version

<details>
<summary>Details</summary>

#### Manual

All the shim binaries are identical, with the only difference being the name of the node binary to shim.

##### Download distributable

Get specific `shim` version from the [releases page](https://github.com/iamogbz/nvmshim/releases).

##### Ensure downloaded file can be executed

```sh
chmod +x shim
```

##### Copy binary into your nvshim install path

```sh
mkdir -p ~/.nvm/shims
```

```sh
cp shim ~/.nvm/shims/node
cp shim ~/.nvm/shims/npm
cp shim ~/.nvm/shims/npx
```

##### Add install folder to `PATH` in your shell config profile

```sh
export PATH="~/.nvm/shims:$PATH"
```

</details>

### Build

This requires having `git` and `make` configured for your terminal.

#### Clone and navigate into repo

```sh
git clone git@github.com:iamogbz/nvshim.git && cd nvmshim
```

#### Install dependencies

```sh
make install
```

#### Build distributable binaries

```sh
make build
```

#### Run installer

With the environment variables as the [install script](#script).

##### Example

```sh
env NVSHIM_DIR=~/.nvm/shims PROFILE=~/.config/fish/config.fish dist/installer
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
make tests
```
