import re 

with open('agent-bio.txt', 'r', encoding='utf-8') as file:
    content = file.read()

content = content.replace('\n', '').replace('\r', '').replace('"', "'").replace(',,', ',')
content = ''.join(char for char in content if ord(char) < 128)
content = re.sub(' {4,}', '    ', content)

with open('agent-bio.txt', 'w', encoding='utf-8') as file:
    file.write(content)