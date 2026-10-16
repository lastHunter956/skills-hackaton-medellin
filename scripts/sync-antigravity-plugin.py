#!/usr/bin/env python3
"""Script de sincronización idempotente para el plugin AGY open-payments-guardrails.

Copia las 8 skills canónicas desde skills/ hacia plugins/open-payments-guardrails/skills/,
asegurando que el plugin sea 100% autosuficiente para distribución independiente
sin dependencias de enlaces simbólicos locales ni rutas absolutas.
"""

import argparse
import os
import shutil
import sys

REQUIRED_SKILLS = [
    "incoming-payments-checkout",
    "interledger-protocol-fundamentals",
    "nextjs-typescript-application-architect",
    "open-payments-transfers",
    "rafiki-local-playground",
    "server-only-payments-client",
    "skill-authoring-standard",
    "webhook-signature-verification",
]


def sync_plugin_skills(repo_root, dry_run=False):
    repo_root = os.path.abspath(repo_root)
    source_dir = os.path.join(repo_root, "skills")
    target_dir = os.path.join(repo_root, "plugins", "open-payments-guardrails", "skills")

    if not os.path.isdir(source_dir):
        print(f"ERROR: Directorio fuente {source_dir} no existe.")
        return 1

    missing = [s for s in REQUIRED_SKILLS if not os.path.isdir(os.path.join(source_dir, s))]
    if missing:
        print(f"ERROR: Faltan skills requeridas en {source_dir}: {missing}")
        return 1

    print(f"Fuente canónica: {source_dir}")
    print(f"Destino plugin:  {target_dir}")
    print(f"Modo: {'DRY-RUN' if dry_run else 'EJECUCIÓN'}")

    copied = 0
    for s_name in REQUIRED_SKILLS:
        s_src = os.path.join(source_dir, s_name)
        s_dst = os.path.join(target_dir, s_name)

        if dry_run:
            print(f" [PLAN] Sincronizar: {s_name} -> {s_dst}")
            copied += 1
            continue

        os.makedirs(target_dir, exist_ok=True)
        # Limpieza previa del destino específico para evitar archivos residuales
        if os.path.exists(s_dst):
            shutil.rmtree(s_dst)

        shutil.copytree(s_src, s_dst)
        print(f" [OK] Sincronizada: {s_name}")
        copied += 1

    print(f"\nResumen: {copied}/{len(REQUIRED_SKILLS)} skills sincronizadas exitosamente.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza skills canónicas al plugin Antigravity open-payments-guardrails."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Ruta raíz del repositorio (por defecto: .)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el plan de sincronización sin realizar cambios.",
    )
    args = parser.parse_args()
    sys.exit(sync_plugin_skills(args.root, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
