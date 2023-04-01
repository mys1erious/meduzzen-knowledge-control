#!/usr/bin/env bash


# To start from main.py
 exec uvicorn app.main:app --host 0.0.0.0 --port 8000
