import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
