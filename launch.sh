#!/bin/bash

cd "$(dirname "$0")" || exit

source venv/bin/activate
python server.py