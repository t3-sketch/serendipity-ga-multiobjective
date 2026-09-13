#!/bin/sh
# Block until every arm has written completion.json, then produce the tables.
# Prints one line per state change so the log doubles as a progress record.
cd "$(dirname "$0")" || exit 1
runs="A1-sasrec-scratch A2-comirec-sa A3-esasrec"

while :; do
  pending=""
  for run in $runs; do
    [ -f "outputs/$run/completion.json" ] || pending="$pending $run"
  done
  [ -z "$pending" ] && break
  if [ "$pending" != "$last" ]; then
    echo "[$(date '+%H:%M:%S')] waiting for:$pending"
    last="$pending"
  fi
  if ! pgrep -f "experiment.py --config" > /dev/null; then
    echo "[$(date '+%H:%M:%S')] no experiment process is alive but$pending is unfinished"
    exit 1
  fi
  sleep 60
done

echo "[$(date '+%H:%M:%S')] all arms complete; analysing"
.venv/bin/python -B analyze.py
