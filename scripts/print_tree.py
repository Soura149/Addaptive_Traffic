import os

def generate_tree(dir_path, prefix=""):
    # Folders to ignore for a cleaner output
    ignore_dirs = {'.git', '__pycache__', 'donotuse'}
    
    entries = sorted(os.listdir(dir_path))
    
    # Filter out ignored directories
    entries = [e for e in entries if not (os.path.isdir(os.path.join(dir_path, e)) and e in ignore_dirs)]
    
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        is_last = i == (len(entries) - 1)
        
        # Build the line to print
        connector = "\\-- " if is_last else "+-- "
        print(prefix + connector + entry)
        
        if os.path.isdir(path):
            extension = "    " if is_last else "|   "
            generate_tree(path, prefix=prefix + extension)

if __name__ == "__main__":
    print(".")
    generate_tree(".")
