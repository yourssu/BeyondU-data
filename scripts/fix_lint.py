
import sys
from pathlib import Path

def fix_lint(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    count = 0
    for line in lines:
        if not line.strip(): # If line is empty or whitespace only
            if len(line) > 1: # If it contains whitespace (more than just newline)
                fixed_lines.append('\n') # Replace with just newline
                count += 1
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {count} lines in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            fix_lint(f)
    else:
        print("Usage: python fix_lint.py <file1> <file2> ...")
