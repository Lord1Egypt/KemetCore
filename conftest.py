"""Pytest bootstrap: put every project's golden/ and pymodel/ dir on sys.path.

Module files are uniquely prefixed per project (e.g. hapi_fpu, bast_matmul) so
there are no cross-project import collisions. Tests can simply `import hapi_fpu`.
"""
import glob
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
for _sub in (glob.glob(os.path.join(_ROOT, "projects", "*", "golden")) +
             glob.glob(os.path.join(_ROOT, "projects", "*", "pymodel"))):
    if _sub not in sys.path:
        sys.path.insert(0, _sub)
