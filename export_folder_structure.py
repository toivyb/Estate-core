import os

EXCLUDE_DIRS = {"venv", "__pycache__", ".git", ".mypy_cache"}

def write_structure(base_path):
    txt_path = os.path.join(base_path, "structure.txt")
    tree_path = os.path.join(base_path, "structure.tree")

    def generate_structure():
        lines = []
        for dirpath, dirnames, filenames in os.walk(base_path):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            level = dirpath.replace(base_path, "").count(os.sep)
            indent = "│   " * level + "├── "
            lines.append(f"{indent}{os.path.basename(dirpath)}/")
            sub_indent = "│   " * (level + 1) + "├── "
            for file in filenames:
                lines.append(f"{sub_indent}{file}")
        return "\n".join(lines)

    structure_output = generate_structure()

    with open(txt_path, "w", encoding="utf-8") as f_txt, open(tree_path, "w", encoding="utf-8") as f_tree:
        f_txt.write(structure_output)
        f_tree.write(structure_output)

    print(f"[✓] Exported to:\n - {txt_path}\n - {tree_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    write_structure(current_dir)
