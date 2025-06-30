#!/bin/bash

# This is the fix.
# We are telling the Python interpreter to add the './app' directory
# to the list of places it looks for modules.
export PYTHONPATH="${PYTHONPATH}:."

# Now when Gunicorn runs your app and your app tries to import 'validation',
# Python will know to look inside the 'app' directory and will find it.
gunicorn --worker-class uvicorn.workers.UvicornWorker app.myapp:app
