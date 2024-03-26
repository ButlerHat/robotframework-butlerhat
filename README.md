# ButlerHat for RobotFramework

Libraries for data collection and inference with Robot Framework

## Stealth mode

First you need to set an environmen variable:

```
export PIP_EXTRA_INDEX_URL=https://pypiserver.paipaya.com/simple/
```

To use stealth mode you need an user and password for pypiserver. Ask the administrator to get it.

Install with:
```
pip install --extra-index-url https://<USER>:<PASS>@pypiserver.paipaya.com/ robotframework-butlerhat[browser_stealth]
```
For develop
```
pip install -e /workspaces/ai-butlerhat/data-butlerhat/robotframework-butlerhat[stealth_browser]
```

Check more documentation of how place credentials to download here:
https://github.com/pypiserver/pypiserver/tree/master#Uploading-Packages-Remotely

---

# Changes in Version 0.2

In version 0.2, we have discontinued the use of the pickle format for saving data. As a result, .pickle files created with previous versions will not be loadable with this version. This is due to changes in the `SaveStatus` class, where the enum has been modified.

---

# Contribute

1. Semantic Versioning
We use Semantic Versioning. Versions are formatted as MAJOR.MINOR.PATCH:

- MAJOR: Backward-incompatible updates.
- MINOR: New, backward-compatible features.
- PATCH: Backward-compatible bug fixes.

2. Git Tags for Releases
To create a release:

```bash
git tag -a v<version> -m "Release version <version>"
git push --tags
```

Replace `<version>` with the appropriate version number.

3. Automatic Version Management
Ensure setuptools_scm is installed and configured:

```bash
pip install setuptools_scm
```

In setup.py:

```python
from setuptools import setup
setup(
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    # other settings
)
```