#!/bin/bash

pycallgraph graphviz --output-format=dot --output-file=cg_codememo.dot -- launch_app.py
