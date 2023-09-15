import os

# Step 1: Get the list of installed packages using pip freeze and write them to requirements.txt
os.system('pip freeze > requirements.txt')

# Step 2: Check the dependencies for known security vulnerabilities using safety
os.system('safety check -r requirements.txt')

# Step 3: Perform a static analysis of all Python scripts in the current directory using bandit to find common security issues
os.system('bandit -r .')

# Step 4: Clean up
os.remove('requirements.txt')
