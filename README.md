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