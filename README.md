# NVM Shim

<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="360" height="180" viewBox="0 0 480 240">
  <defs>
    <linearGradient id="linear-gradient" x1="0.5" y1="0.5" x2="0.5" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0" stop-color="#64af7b"/>
      <stop offset="1" stop-color="#418164"/>
    </linearGradient>
  </defs>
  <g id="Group_1" data-name="Group 1" transform="translate(-16 -136)">
    <rect id="Rectangle_1" data-name="Rectangle 1" width="480" height="240" rx="15" transform="translate(16 136)" fill="url(#linear-gradient)"/>
    <line id="Line_7" data-name="Line 7" y1="180" transform="translate(316 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <line id="Line_8" data-name="Line 8" y1="180" transform="translate(346 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <line id="Line_9" data-name="Line 9" y1="180" transform="translate(376 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <line id="Line_10" data-name="Line 10" y1="180" transform="translate(406 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <line id="Line_11" data-name="Line 11" y1="180" transform="translate(436 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <line id="Line_12" data-name="Line 12" y1="180" transform="translate(466 166)" fill="none" stroke="#fff" stroke-linecap="square" stroke-width="15"/>
    <path id="Path_1" data-name="Path 1" d="M76,166l90,180,90-180" fill="none" stroke="#fff" stroke-linecap="square" stroke-linejoin="bevel" stroke-width="15"/>
    <path id="Path_2" data-name="Path 2" d="M166,346V166l90,180" transform="translate(-120)" fill="none" stroke="#fff" stroke-linecap="square" stroke-linejoin="bevel" stroke-width="15"/>
    <path id="Path_3" data-name="Path 3" d="M256,346V166L166,346" transform="translate(30)" fill="none" stroke="#fff" stroke-linecap="square" stroke-linejoin="bevel" stroke-width="15"/>
  </g>
</svg>

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
