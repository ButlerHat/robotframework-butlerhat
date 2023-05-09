#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import argparse


parser = argparse.ArgumentParser(description='Resolve conda secret')
parser.add_argument('--token', default=None, help='GitHub access token')
args = parser.parse_args()

try:
    token = args.token if args.token else os.environ["GITHUB_ACCESS_TOKEN"]
except KeyError:
    print("Please set the environment variable GITHUB_ACCESS_TOKEN or set --token argument")
    exit(1)

replacements = {
    "{GITHUB_ACCESS_TOKEN}": args.token
}

with open("conda.yaml", "r") as infile, open("conda_pass.yaml", "w") as outfile:
    # Read the content of the input file
    filedata = infile.read()
    # Replace the variables with their values
    for src, target in replacements.items():
        filedata = filedata.replace(src, target)
    # Write the modified content to the output file
    outfile.write(filedata)
