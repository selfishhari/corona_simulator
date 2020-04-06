#!/usr/bin/env bash
while : ; do
	date
    python update-all.py
    date
    echo "sleep 1 hour"
    sleep 1h
done
