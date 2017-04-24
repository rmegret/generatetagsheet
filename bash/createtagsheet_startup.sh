#!/bin/bash


if [[ "$0" == "$BASH_SOURCE" ]]; then
    echo "Usage: script needs to be sourced:"
    echo "  source generatetagsheet_activate"
    echo ""
    echo "  Add generatetagsheet tools in PATH"
    exit
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PATH="${DIR}:${PATH}"
