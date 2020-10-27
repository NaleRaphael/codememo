# codememo
[![Build Status](https://travis-ci.com/NaleRaphael/codememo.svg?token=zhYrgBMjb73CEWtXQwny&branch=master)](https://travis-ci.com/NaleRaphael/codememo)
[![codecov](https://codecov.io/gh/NaleRaphael/codememo/branch/master/graph/badge.svg)](https://codecov.io/gh/NaleRaphael/codememo)
[![release](https://img.shields.io/github/release/naleraphael/codememo.svg?color=blue)](https://github.com/NaleRaphael/codememo/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A note taking tool helps you trace code.

![screenshot](images/codememo_screenshot_01.png)


## Requirements
### Minimal requirements
- `imgui[pyglet] >= 1.2.0`
- `pyperclip >= 1.8.0`

    This is required for linux users only, because facilities for accessing system clipboard are not supported in the intergrated backend `pyglet` currently.

    And note that `xclip` should be installed in system (if not, you can install it by `$ sudo apt-get install xclip`).

### Use a patch for multiline input textbox
- `Cython >= 0.29.21`

It requires to install `Cython` in order to re-compile `pyimgui`. But you don't need to install it manually, all necessary setups will be handled by `setup.py`. 

### Import from call graphs
- `pygraphviz >= 1.6`
- `networkx >= 2.5`

Currently, DOT file for call graph is supported. You can install these dependencies with syntax `$ pip install THIS_PACAKGE[dot]`, see also [instructions for installtion](#Installation). But note that:
- Content (code snippet) won't be available since call graph is
  targeted to represent relations between functions.
- Since our implementaion of node is a single-root node structure,
  those multi-root (multi-parent) nodes in call graph will be
  separated into multiple single-root nodes. e.g.


## Installation
- Basic installation
    ```bash
    $ git clone https://github.com/naleraphael/codememo
    $ cd codememo

    # (recommended) install with forked version of `pyimgui`
    $ pip install ./
    # ... or install with orignal version of `pyimgui`
    # $ pip install -v --global-option="--use-original-pyimgui" ./
    ```

- (Extras) support for creating projects from call graphs
    ```bash
    $ pip install .[dot]

    # if you are using zsh, you have to escape square brackets
    # $ pip install .\[dot\]
    ```

    For linux users, `libgraphviz-dev` is required before installing `pygraphviz`. You might need to install it by `$ sudo apt-get install libgraphviz-dev`.

    For non-linux users, `pygraphviz` have to be installed manually since it has to be built with source of `graphviz`. If you don't want to be bothered by those complicated settings, you can simply install it through a forked version provided by Alex Lubbock on Anaconda: `$ conda install pygraphviz -c alubbock`. See also [this comment](https://github.com/pygraphviz/pygraphviz/issues/186#issuecomment-481760487) for further details.

## Usage
- Launch GUI
    ```bash
    $ python -m codememo
    ```


## Note
- This project is still under development, but please feel free to use it and give us feedback. ;)
- Configuration files and crash dump files will be stored under the folder `$HOME/.codememo`.
