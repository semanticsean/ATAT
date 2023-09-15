import subprocess

# Step 1: Running Pytest along with Coverage
try:
    subprocess.run(["pytest", "--cov=your_package_name"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Tests failed: {e}")
except FileNotFoundError:
    print("Pytest not found. Please install pytest and pytest-cov packages.")

# Step 2: Generating a Coverage Report
try:
    subprocess.run(["coverage", "report", "-m"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Could not generate coverage report: {e}")
except FileNotFoundError:
    print("Coverage.py not found. Please install the coverage package.")
