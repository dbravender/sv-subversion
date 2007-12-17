
"""sv test suite.

run with:

$ nosetests

"""
import sys, os

def setup():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
