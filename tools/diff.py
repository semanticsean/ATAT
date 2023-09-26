import sys
import difflib
import datetime

def generate_diff(file1, file2, output_file):
    """
    Generates a diff of two files and writes the result to an output file.
    :param file1: The path to the first file.
    :param file2: The path to the second file.
    :param output_file: The path to the output file where the diff will be written.
    """
    # Read the content of both files
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        file1_content = f1.readlines()
        file2_content = f2.readlines()

    # Generate the diff with line numbers and labels
    d = difflib.unified_diff(
        file1_content, file2_content,
        fromfile=file1, tofile=file2, 
        lineterm='',   # This removes an extra newline
        n=0   # Provides context. Setting to 0 shows only the lines that have changed.
    )

    # Write the diff to the output file
    with open(output_file, 'w') as out:
        # Add meta data to the top of the output
        out.write(f"Diff generated on: {datetime.datetime.now()}\n")
        out.write(f"Comparing {file1} to {file2}\n")
        out.write('-' * 80 + '\n')
        
        for line in d:
            out.write(line + '\n')  # Add newline as lineterm='' above removes it

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: diff_script.py <file1> <file2> <output_file>")
        sys.exit(1)

    file1, file2, output_file = sys.argv[1], sys.argv[2], sys.argv[3]
    generate_diff(file1, file2, output_file)
    print(f"Diff saved to {output_file}")
