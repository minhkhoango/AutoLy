#!/bin/bash

# No more 'cd'. No more 'PYTHONPATH'.
# Just the standard, professional way to run a packaged Python app.
# The format is [package_name].[module_name]:[app_variable]
gunicorn --worker-class uvicorn.workers.UvicornWorker app.myapp:app