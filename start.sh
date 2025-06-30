#!/bin/bash

# This command tells Gunicorn to start your app.
# It will run the 'app' object inside the 'myapp.py' file.
# The --worker-class uvicorn.workers.UvicornWorker line is standard for NiceGUI.
gunicorn --worker-class uvicorn.workers.UvicornWorker myapp:app
