"""Local training and evaluation harness for Video2Knowledge.

Importing the package puts the pinned backend snapshot on sys.path, so the
team's feature extractors and classifiers are used as they are (`import app`).
"""
from v2k.env import use_backend

use_backend()
