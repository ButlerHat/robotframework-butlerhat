#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess


replacements = {
    "{GITHUB_ACCESS_TOKEN}": os.environ["GITHUB_ACCESS_TOKEN"]
}


with open("conda.yaml", "r") as infile, open("conda_pass.yaml", "w") as outfile:
    # Read the content of the input file
    filedata = infile.read()
    # Replace the variables with their values
    for src, target in replacements.items():
        filedata = filedata.replace(src, target)
    # Write the modified content to the output file
    outfile.write(filedata)

# Run ./rcc run
subprocess.run(["./rcc", "run"])
