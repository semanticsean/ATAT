import base64
import os

def is_base64_start(line):
    return 'Content-Transfer-Encoding: base64' in line

def is_boundary_line(line):
    return line.startswith('--')

def decode_base64_block(base64_block):
    base64_content = ''.join(base64_block)
    try:
        return base64.b64decode(base64_content).decode('utf-8')
    except Exception as e:
        print(f"Error decoding base64 block: {e}")
        return '\n'.join(base64_block)

def process_file(input_file):
    output_file = input_file.replace('.md', '') + '_converted.md'
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        base64_block = False
        base64_lines = []

        for line in infile:
            if base64_block:
                if is_boundary_line(line):
                    decoded_content = decode_base64_block(base64_lines)
                    outfile.write(decoded_content)
                    outfile.write(line)
                    base64_block = False
                    base64_lines = []
                else:
                    base64_lines.append(line.strip())
            else:
                if is_base64_start(line):
                    base64_block = True
                else:
                    outfile.write(line)

        # In case the file ends while still inside a base64 block
        if base64_block:
            decoded_content = decode_base64_block(base64_lines)
            outfile.write(decoded_content)

    print(f"File processed. Output saved to {output_file}")

# Example usage
process_file('b64input.md')
