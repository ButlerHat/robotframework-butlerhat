# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages  # type: ignore

sys.path.append("ButlerRobot")

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

package_data = {
    "ButlerRobot": [
        "javascript/keywords.js",
        "requirements.txt"
    ],
}

packages = find_packages(exclude=["test", "TestSuites", "ButlerApi"])

install_requires = open(os.path.join("ButlerRobot", "requirements.txt")).readlines()

setup_kwargs = {
    "name": "robotframework-butlerhat",
    "version": "0.1",
    "description": "ButlerHat libraries for data and inference with AI in RobotFramework.",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "ButlerHat",
    "author_email": "d.correas.oliver@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "",
    "packages": packages,
    "install_requires": install_requires,
    "entry_points": {"console_scripts": ["rfbrowser=Browser.entry:main"]},
    "python_requires": ">=3.7,<4.0",
    "classifiers": [
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Testing",
        "Framework :: Robot Framework",
        "Framework :: Robot Framework :: Library",
    ],
    "package_data": package_data,
    "include_package_data": True,
}


setup(**setup_kwargs)