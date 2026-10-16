#!/usr/bin/env python3
"""Linter de contexto y presupuesto de tokens para Antigravity CLI.

Verifica:
- AGENTS.md <= 5000 caracteres
- Suma de rules always_on <= 4000 caracteres
- Cada rule individual <= 6000 caracteres
- Cada rule contiene un campo 'trigger' en su frontmatter
- Toda skill contiene 'description' de <= 400 caracteres
- Todo SKILL.md <= 200 lineas
- No existen carpetas scripts/, examples/ o resources/ vacias
- No existen lineas de >= 80 caracteres duplicadas entre archivos
"""

import argparse
import os
import re
import sys
from collections import defaultdict


def parse_frontmatter(content):
    """Extrae metadatos basicos del YAML frontmatter sin dependencias externas."""
    if not content.startswith("---"):
        return None, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content

    fm_text = parts[1]
    body = parts[2]
    metadata = {}

    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()

            # Bloque multilinea (>- o | o similar)
            if val in (">-", ">", "|", "|-"):
                multiline_vals = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    multiline_vals.append(lines[i].strip())
                    i += 1
                metadata[key] = " ".join([v for v in multiline_vals if v]).strip()
                continue
            else:
                # Quitar comillas si las hay
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                metadata[key] = val
        i += 1

    return metadata, body


def check_empty_folders(root_dir):
    """Detecta carpetas scripts/, examples/ o resources/ que esten vacias."""
    problems = []
    target_names = {"scripts", "examples", "resources"}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Excluir .git y node_modules
        if "/.git" in dirpath or "/node_modules" in dirpath:
            continue
        base = os.path.basename(dirpath)
        if base in target_names:
            visible_files = [f for f in os.listdir(dirpath) if not f.startswith(".")]
            if len(visible_files) == 0:
                rel_path = os.path.relpath(dirpath, root_dir)
                problems.append(f"Carpeta vacia detectada: {rel_path}/")
    return problems


def lint_context(root_dir):
    """Ejecuta todas las validaciones de contexto y presupuesto."""
    problems = []
    root_dir = os.path.abspath(root_dir)

    # 1. Validar AGENTS.md
    agents_path = os.path.join(root_dir, "AGENTS.md")
    if os.path.exists(agents_path):
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 5000:
            problems.append(f"AGENTS.md excede presupuesto: {len(content)} caracteres (maximo 5000)")

    # 2. Validar Rules en .agents/rules y .agent/rules
    rule_dirs = [
        os.path.join(root_dir, ".agents", "rules"),
        os.path.join(root_dir, ".agent", "rules"),
    ]
    always_on_total_chars = 0
    rule_files = []

    for r_dir in rule_dirs:
        if os.path.isdir(r_dir):
            for fname in sorted(os.listdir(r_dir)):
                if fname.endswith(".md"):
                    rule_files.append(os.path.join(r_dir, fname))

    for r_path in rule_files:
        rel_r_path = os.path.relpath(r_path, root_dir)
        with open(r_path, "r", encoding="utf-8") as f:
            content = f.read()

        char_count = len(content)
        if char_count > 6000:
            problems.append(f"Rule {rel_r_path} excede limite individual: {char_count} caracteres (maximo 6000)")

        fm, body = parse_frontmatter(content)
        if not fm or "trigger" not in fm or not fm["trigger"].strip():
            problems.append(f"Rule {rel_r_path} no tiene trigger en su frontmatter")
        else:
            trigger_val = fm["trigger"].strip()
            if trigger_val == "always_on":
                always_on_total_chars += char_count

    if always_on_total_chars > 4000:
        problems.append(
            f"Reglas always_on exceden presupuesto combinado: {always_on_total_chars} caracteres (maximo 4000)"
        )

    # 3. Validar Skills en .agents/skills y .agent/skills
    skill_dirs = [
        os.path.join(root_dir, ".agents", "skills"),
        os.path.join(root_dir, ".agent", "skills"),
    ]
    for s_dir in skill_dirs:
        if os.path.isdir(s_dir):
            for skill_name in sorted(os.listdir(s_dir)):
                skill_path = os.path.join(s_dir, skill_name)
                if os.path.isdir(skill_path):
                    skill_md = os.path.join(skill_path, "SKILL.md")
                    if os.path.exists(skill_md):
                        rel_skill_md = os.path.relpath(skill_md, root_dir)
                        with open(skill_md, "r", encoding="utf-8") as f:
                            s_content = f.read()

                        line_count = len(s_content.splitlines())
                        if line_count > 200:
                            problems.append(
                                f"Skill {rel_skill_md} excede 200 lineas: {line_count} lineas"
                            )

                        fm, _ = parse_frontmatter(s_content)
                        if not fm or "description" not in fm or not fm["description"].strip():
                            problems.append(f"Skill {rel_skill_md} no tiene description en su frontmatter")
                        else:
                            desc = fm["description"].strip()
                            if len(desc) > 400:
                                problems.append(
                                    f"Skill {rel_skill_md} description excede 400 caracteres: {len(desc)} caracteres"
                                )

    # 4. Validar carpetas scripts/examples/resources vacias
    empty_folder_problems = check_empty_folders(root_dir)
    problems.extend(empty_folder_problems)

    # 5. Validar lineas duplicadas de >= 80 caracteres entre archivos .md
    line_origins = defaultdict(set)
    for dirpath, _, filenames in os.walk(root_dir):
        if "/.git" in dirpath or "/node_modules" in dirpath or "/.next" in dirpath or "/plugins" in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(".md"):
                file_full = os.path.join(dirpath, fname)
                rel_f = os.path.relpath(file_full, root_dir)
                try:
                    with open(file_full, "r", encoding="utf-8") as f:
                        header = f.readline()
                        if "AUTOGENERATED" in header:
                            continue
                        f.seek(0)
                        for idx, line in enumerate(f, 1):
                            stripped = line.strip()
                            if len(stripped) >= 80:
                                line_origins[stripped].add(rel_f)
                except Exception:
                    pass

    for line_text, files in line_origins.items():
        if len(files) > 1:
            preview = (line_text[:75] + "...") if len(line_text) > 75 else line_text
            file_list = ", ".join(sorted(files))
            problems.append(
                f"Linea de >=80 caracteres duplicada en ({file_list}): \"{preview}\""
            )

    return problems


def main():
    parser = argparse.ArgumentParser(
        description="Linter de presupuesto de tokens y reglas de contexto para Antigravity CLI."
    )
    parser.add_argument(
        "root_dir",
        nargs="?",
        default=".",
        help="Ruta raiz del repositorio a verificar (por defecto: directorio actual).",
    )
    args = parser.parse_args()

    problems = lint_context(args.root_dir)

    if problems:
        print("FALLO: Se encontraron problemas en el contexto:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    else:
        print("OK: dentro de presupuesto")
        sys.exit(0)


if __name__ == "__main__":
    main()
