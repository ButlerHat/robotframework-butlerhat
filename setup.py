# -*- coding: utf-8 -*-
import sys
import os
from setuptools import setup, find_packages  # type: ignore

sys.path.append("ButlerRobot")

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

package_data = {
    "ButlerRobot": [
        "javascript/keywords.js"
    ],
}

# IMPORTANT
# If the extras change, change also robotframework-dist-butlerhat
base_requires = [
    'wheel',
    'imagehash',
    'Pillow'  # For image conversion in screenshots
]

full_requires = base_requires + [
    'robotframework>=5.0.1', 
    'rpaframework>=23.3.0',
    'robotframework-browser>=16.0.5',
    'robotframework-seleniumlibrary',
    'fastdeploy-python',  # To consult OCR
    'cryptography',  # For vault in automation
    'pyautogui'  # For desktop scroll
]

browser_requires = base_requires + [
    'robotframework>=6.1.1',
    'robotframework-browser>=17.2.0',
    'fastdeploy-python',  # To consult OCR
    'cryptography',  # For vault in automation
]

# This version requires to export PIP_EXTRA_INDEX_URL https://<USER>:<PASS>@pypiserver.paipaya.com/
browser_stealth_requires = base_requires + [
    'robotframework>=6.1.1',
    'robotframework-browser-stealth',
    'fastdeploy-python',  # To consult OCR
    'cryptography',  # For vault in automation
]

selenium_requires = base_requires + [
    'robotframework>=6.1.1',
    'robotframework-seleniumlibrary>=5.1.3',
    'fastdeploy-python',  # To consult OCR
    'cryptography',  # For vault in automation
]


packages = find_packages(exclude=[
    "test", 
    "TestSuites", 
    "ButlerApi", 
    "robotframework-browser-stealth"
])

setup_kwargs = {
    "name": "robotframework-butlerhat",
    # "version": "0.2",
    "description": "ButlerHat libraries for data and inference with AI in RobotFramework.",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "ButlerHat",
    "author_email": "d.correas.oliver@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "",
    "use_scm_version": True,
    "setup_requires": ["setuptools_scm"],
    "packages": packages,
    "install_requires": base_requires,
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
    "extras_require": {
        "full": full_requires,
        "browser": browser_requires,
        "selenium": selenium_requires,
        "browser_stealth": browser_stealth_requires
    },
}

setup(**setup_kwargs)
