import os
import shutil

repo_root = r"C:\Large_files\opsGaurd\coralSync"

# 1. Rename directories if they exist
dir_renames = [
    (os.path.join(repo_root, "opsGaurd-api", "src", "coral_sync_api"), os.path.join(repo_root, "opsGaurd-api", "src", "coral_sync_api")),
    (os.path.join(repo_root, "agent", "src", "coral_sync_agent"), os.path.join(repo_root, "agent", "src", "coral_sync_agent")),
    (os.path.join(repo_root, "opsGaurd-api"), os.path.join(repo_root, "coral-sync-api")),
    (os.path.join(repo_root, "opsGaurd-ui"), os.path.join(repo_root, "coral-sync-ui"))
]

for src, dst in dir_renames:
    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst)

# 2. String replacements across files
replacements = {
    'coral-sync-api': 'coral-sync-api',
    'coral-sync-ui': 'coral-sync-ui',
    'coralSync': 'coralSync',
    'coralsync': 'coralsync',
    'CORALSYNC': 'CORALSYNC',
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
