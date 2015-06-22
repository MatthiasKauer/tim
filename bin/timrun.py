"""
starter script to be used during development (where paths would otherwise be messed up)

    :copyright: 2015 by Matthias Kauer
    :license: BSD
"""
import sys

try:
    import _preamble
except ImportError:
    sys.exit(-1)

from tim.timscript import main
main()
