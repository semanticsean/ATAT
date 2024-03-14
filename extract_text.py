import os
import textract

def extract_and_save_text(file_path):
    text = textract.process(file_path).decode('utf-8')
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join('agents/new_agent_files', file_name + '.txt')
    with open(output_path, 'w') as file:
        file.write(text)