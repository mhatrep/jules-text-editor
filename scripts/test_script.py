import sys
import time
print("Hello from Python!")
print(f"Arguments: {sys.argv[1:]}")
for i in range(5):
    print(f"Python count: {i}")
    time.sleep(0.2)
print("Python script finished.")
sys.stderr.write("This is a Python stderr message.\n")
