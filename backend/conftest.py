import sys
import os

# Ensure backend is on path so all imports resolve as "app.xxx" — never duplicated
sys.path.insert(0, os.path.dirname(__file__))
