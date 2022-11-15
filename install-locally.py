#!/bin/sh
. ./set-ex.sh

WHAT=umlsequence2

./build.sh

yes | pip3 uninstall $WHAT 2>/dev/null || true
yes | sudo pip3 uninstall $WHAT

python3 setup.py build

sudo python3 setup.py install
