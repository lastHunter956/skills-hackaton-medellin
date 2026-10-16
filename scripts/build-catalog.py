#!/usr/bin/env python3
"""Generador de catálogo de skills en Markdown desde los frontmatter de SKILL.md."""

import argparse
import os
import re
import sys


def parse_frontmatter(content):
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    fm_text = parts[1]
    metadata = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            if val in (">-", ">", "|", "|-"):
                multiline_vals = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    multiline_vals.append(lines[i].strip())
                    i += 1
                metadata[key] = " ".join([v for v in multiline_vals if v]).strip()
                continue
            else:
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                metadata[key] = val
        i += 1
    return metadata


def build_catalog(skills_dir):
    skills_dir = os.path.abspath(skills_dir)
    if not os.path.isdir(skills_dir):
        print(f"ERROR: Directorio {skills_dir} no existe.")
        return 1

    rows = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_md = os.path.join(item_path, "SKILL.md")
            if os.path.isfile(skill_md):
                with open(skill_md, "r", encoding="utf-8") as f:
                    fm = parse_frontmatter(f.read())
                if fm:
                    name = fm.get("name", item)
                    desc = fm.get("description", "").replace("\n", " ")
                    rows.append(f"| `{name}` | {desc} |")

    table = [
        "| Skill | Descripción y Alcance |",
        "| :--- | :--- |",
    ] + rows

    catalog_md = "\n".join(table)
    print(catalog_md)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Genera tabla de catálogo en Markdown a partir de los frontmatter de SKILL.md."
    )
    parser.add_argument(
        "--skills-dir",
        default=".agents/skills",
        help="Ruta al directorio de skills (por defecto: .agents/skills)",
    )
    args = parser.parse_args()
    sys.exit(build_catalog(args.skills_dir))


if __name__ == "__main__":
    main()
