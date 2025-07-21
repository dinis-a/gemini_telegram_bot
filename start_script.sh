#!/bin/bash

python3 /app/main.py &

wait -n

# Exit with status of process that exited first
exit $?

