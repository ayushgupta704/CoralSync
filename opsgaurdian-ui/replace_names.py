import os

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    new_content = content.replace('opsGaurdian', 'opsGaurdian')
    new_content = new_content.replace('opsgaurdian', 'opsgaurdian')
    new_content = new_content.replace('OPSGAURDIAN', 'OPSGAURDIAN')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith(('.ts', '.tsx', '.html', '.css', '.json')):
            replace_in_file(os.path.join(root, file))
