import subprocess
import time
import os

os.chdir('C:\\Disk\\terminal game')

# Open two terminals running the game
subprocess.Popen(['wt', 'python', 'main.py'])
time.sleep(0.1)
subprocess.Popen(['wt', 'python', 'main.py'])

print("Two game instances launched!")