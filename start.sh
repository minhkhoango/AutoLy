#!/bin/bash

# 1. Walk into the room where the code lives.
cd app

# 2. Now, run the app. Python will find all its sibling files.
gunicorn --worker-class uvicorn.workers.UvicornWorker myapp:app