# -*- coding: utf-8 -*-
"""Helper module to allow calling package as a script via 'python -m'."""

from __future__ import absolute_import, print_function, unicode_literals

from .main import main

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]) or 0)
