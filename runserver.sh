#!/bin/bash
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

$SCRIPTPATH/env/bin/gunicorn app:app -b 127.0.0.1:$PORT -n "Senior compliments"

