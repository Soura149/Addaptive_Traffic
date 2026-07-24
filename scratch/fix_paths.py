import os

directory = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic\scripts"
old_path = r"C:\VSCODE\CISInternship_Implement"
new_path = r"C:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"

for root, _, files in os.walk(directory):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            if old_path in content:
                content = content.replace(old_path, new_path)
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated {f}")
