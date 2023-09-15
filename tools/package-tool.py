import os
import shutil
from pip._internal.operations.freeze import freeze

# Step 1: Get the dependencies of main.py using pipreqs
os.system('pipreqs ./ --force')

# Step 2: Create a folder to store the main.py and its dependencies
os.makedirs('package_folder', exist_ok=True)
shutil.copy('main.py', 'package_folder')

# Step 3: Install the dependencies in the package_folder
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

for req in requirements:
    os.system(f'pip install {req} -t package_folder')

# Step 4: Create a zip file containing the package_folder
shutil.make_archive('package_zip', 'zip', 'package_folder')

# Step 5: Clean up
shutil.rmtree('package_folder')
os.remove('requirements.txt')
