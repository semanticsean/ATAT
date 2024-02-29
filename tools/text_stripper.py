import re

def clean_text_file(input_file_path, output_file_path):
    # Open the input file and read the contents
    with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()

    # Remove all non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Replace line breaks and paragraph breaks with a space
    text = text.replace('\n', ' ').replace('\r', '')

    # Remove special characters except basic punctuation (.,!?)
    text = re.sub(r'[^a-zA-Z0-9 .,!?]', '', text)

    # Write the cleaned text to the output file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(text)

# Example usage
input_file_path = 'file.txt'  # Change this to your input file path
output_file_path = 'output_file.txt'  # Change this to your desired output file path

clean_text_file(input_file_path, output_file_path)
