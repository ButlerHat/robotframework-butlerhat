import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
# Add it to PYTHONPATH environment variable if not exists
if os.environ.get("PYTHONPATH") is None or os.path.dirname(os.path.realpath(__file__)) not in os.environ["PYTHONPATH"]:
    if os.environ.get("PYTHONPATH") is None:
        os.environ["PYTHONPATH"] = ""
    os.environ["PYTHONPATH"] += os.path.dirname(os.path.realpath(__file__))
    print(f"Added {os.path.dirname(os.path.realpath(__file__))} to PYTHONPATH")

