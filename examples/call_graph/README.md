# Example: generate a call graph and load it into codememo
## Prerequisites
- Please make sure `graphviz` and `libgraphbiz-dev` have been install on your system.
- `codememo` should be installed with the option `[dot]`. i.e. It's install with
    the following command:
    ```bash
    $ pip install .[dot]

    # if you are using zsh, you have to escape square brackets
    # $ pip install .\[dot\]
    ```

## Usage
1. Run the bash script `generate_call_graph.sh`.
2. Close the app window `codememo` after it's launched.
3. Then there should be a file called `cg_codememo.dot` generated in this folder.
4. Launch `codememo` again. (`python -m codememo`)
5. Click `import` button -> `From .dot` -> enter the file name `cg_codememo.dot` -> press Enter key.
6. Then the call graph should be imported.
