#!/bin/bash
cd "$(dirname "$0")"
exec python3 watch.py >> ./watcher.log 2>&1
