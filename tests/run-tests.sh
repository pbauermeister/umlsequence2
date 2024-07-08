#!/bin/bash
. ../set-ex.sh

#python3 tests/unit_tests.py -v

for f in test*.umlsequence; do
    umlsequence2 $f
done

rm -f test*.svg
