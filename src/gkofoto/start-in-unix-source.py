#! /usr/bin/env python

import os
import sys

# Find bindir when started via a symlink.
if os.path.islink(sys.argv[0]):
    link = os.readlink(sys.argv[0])
    absloc = os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]), link))
    bindir = os.path.dirname(absloc)
else:
    bindir = os.path.dirname(sys.argv[0])

# Find kofoto libraries (../lib) in the source tree.
sys.path.insert(0, os.path.join(bindir, "..", "lib"))

from gkofoto.main import main
main(bindir, sys.argv)
