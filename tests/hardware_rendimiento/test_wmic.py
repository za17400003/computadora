import subprocess
result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'Name', '/value'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
