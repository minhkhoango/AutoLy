#!/bin/bash

# This command tells Gunicorn to start your app.
# It will run the 'app' variable, which is located inside the 'myapp.py' file,
# which itself is inside the 'app' package.
# The format is: [PACKAGE].[MODULE]:[VARIABLE]
gunicorn --worker-class uvicorn.workers.UvicornWorker app.myapp:app
