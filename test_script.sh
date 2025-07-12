#!/bin/bash
echo "Hello from Shell!"
echo "Arguments: $@"
for i in 1 2 3 4 5
do
    echo "Shell count: $i"
    sleep 0.2
done
echo "Shell script finished." >&2 # Output to stderr
