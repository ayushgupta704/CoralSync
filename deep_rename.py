import os
import shutil

repo_root = r"C:\Large_files\opsGaurd\opsGaurdian"

# 1. Rename directories if they exist
dir_renames = [
    (os.path.join(repo_root, "opsGaurd-api", "src", "opsgaurdian_api"), os.path.join(repo_root, "opsGaurd-api", "src", "opsgaurdian_api")),
    (os.path.join(repo_root, "agent", "src", "opsgaurdian_agent"), os.path.join(repo_root, "agent", "src", "opsgaurdian_agent")),
    (os.path.join(repo_root, "opsGaurd-api"), os.path.join(repo_root, "opsgaurdian-api")),
    (os.path.join(repo_root, "opsGaurd-ui"), os.path.join(repo_root, "opsgaurdian-ui"))
]

for src, dst in dir_renames:
    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst)

# 2. String replacements across files
replacements = {
    'opsgaurdian-api': 'opsgaurdian-api',
    'opsgaurdian-ui': 'opsgaurdian-ui',
    'opsGaurdian': 'opsGaurdian',
    'opsgaurdian': 'opsgaurdian',
    'OPSGAURDIAN': 'OPSGAURDIAN',
    'ayush-gupta': 'ayush-gupta',
    'Ayush Gupta': 'Ayush Gupta',
    'ayushgupta': 'ayushgupta',
    'ayush-gupta': 'ayush-gupta',
    'Ayush Gupta': 'Ayush Gupta Engineering',
    'Ayush Gupta': 'Ayush Gupta', # just in case it was already replaced
}

extensions = ('.ts', '.tsx', '.html', '.css', '.json', '.py', '.md', '.toml', '.yml', '.yaml', '.env', '.env.example', 'LICENSE')

for root, dirs, files in os.walk(repo_root):
    if 'node_modules' in root or '.git' in root or '__pycache__' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith(extensions) or file == 'LICENSE':
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for k, v in replacements.items():
                    new_content = new_content.replace(k, v)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
            except Exception as e:
                pass

print("Complete!")
