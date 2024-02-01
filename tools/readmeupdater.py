import markdown
import os

# Define the paths assuming the script runs from /tools
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)  # This would be the parent directory of /tools, i.e., root
markdown_file_path = os.path.join(root_dir, 'README.md')
templates_dir = os.path.join(root_dir, 'templates')
html_output_path = os.path.join(templates_dir, 'readme.html')

# Make sure the templates directory exists
os.makedirs(templates_dir, exist_ok=True)

# Read the markdown file content
with open(markdown_file_path, 'r') as f:
    markdown_content = f.read()

# Convert markdown content to HTML
html_content = markdown.markdown(markdown_content)

# Write the HTML content to a file in the templates directory
with open(html_output_path, 'w') as f:
    f.write(html_content)

print(f"Converted README.md to HTML and saved as {html_output_path}")
