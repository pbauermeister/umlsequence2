#!/bin/bash
. ./set-ex.sh

WHAT=umlsequence2

#OPTS=--debug
OPTS=

for dir in doc examples; do (
    cd $dir

    rm -f *.svg

    if ls *.md; then
	for doc in *.md; do
	    ../$WHAT $OPTS $doc --markdown
	done
    fi

    if ls *.umlsequence; then
	for doc in *.umlsequence; do
	    ../$WHAT $OPTS $doc
	done
    fi
)
done

./$WHAT README.md --markdown
