#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OllamaTrad - Système de traduction et dialogue avec IA pour le traitement de fichiers JSON

Ce script sert de point d'entrée principal pour l'application OllamaTrad.
Il permet de lancer soit l'interface en ligne de commande, soit l'interface graphique.

Usage:
    python ollamaTrad.py [--gui | --cli] [--file <fichier>] [--command <commande>]

Options:
    --gui           Lance l'interface graphique v2.0
    --cli           Force le mode CLI (priorité sur --gui)
    --file FILE     Fichier JSON à charger au démarrage
    --command CMD   Commande à exécuter directement (CLI seulement)
    --help          Affiche cette aide

Par défaut (sans --gui ni --cli): Lance le CLI

Exemples:
    python ollamaTrad.py                        # Lance le CLI interactif
    python ollamaTrad.py --gui                  # Lance l'interface graphique v2.0
    python ollamaTrad.py --cli --file data.json # Force le CLI avec un fichier
    python ollamaTrad.py --command "ls /"       # Exécute une commande directement
    python ollamaTrad.py --gui --cli            # Force le CLI (--cli prioritaire)
"""

import argparse
import sys
import os
from pathlib import Path

# Configurer l'encodage pour Windows
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Configurer la console Windows pour UTF-8
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(
        description="OllamaTrad - Traitement intelligent de fichiers JSON avec IA",
        epilog="""
Exemples d'utilisation:
  python ollamaTrad.py                     # Lance le CLI interactif (par défaut)
  python ollamaTrad.py --gui               # Lance l'interface graphique
  python ollamaTrad.py --cli               # Force le mode CLI
  python ollamaTrad.py --gui --cli         # Force le CLI (--cli prioritaire)
  python ollamaTrad.py -f data.json        # Charge un fichier au démarrage (CLI)
  python ollamaTrad.py -c "translate /title fr"  # Exécute une commande directement
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Lance l'interface graphique avec formulaire de traduction"
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force le mode CLI (priorité sur --gui si les deux sont présents)"
    )

    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Fichier JSON à charger au démarrage"
    )

    parser.add_argument(
        "--command", "-c",
        type=str,
        help="Commande à exécuter directement (CLI seulement)"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="OllamaTrad 1.0.0"
    )

    args = parser.parse_args()

    # Vérifier que le fichier existe si spécifié
    if args.file and not Path(args.file).exists():
        print(f"❌ Erreur: Le fichier '{args.file}' n'existe pas.")
        sys.exit(1)

    # Déterminer le mode de lancement
    # --cli a priorité sur --gui
    force_cli = args.cli
    launch_gui = args.gui and not force_cli

    # Vérifier que --command n'est pas utilisé avec --gui
    if launch_gui and args.command:
        print("❌ Erreur: --command ne peut pas être utilisé avec --gui")
        sys.exit(1)

    # Avertir si --cli et --gui sont tous les deux présents
    if args.gui and args.cli:
        print("⚠️  Note: --cli et --gui sont tous les deux présents. --cli a priorité, lancement en mode CLI.")

    try:
        if launch_gui:
            # Lancer l'interface graphique
            print(">> Lancement de l'interface graphique OllamaTrad...")

            # Import dynamique pour éviter les erreurs si tkinter n'est pas disponible
            try:
                from gui.app import main as gui_main
                gui_main(args.file)
            except ImportError as e:
                if "tkinter" in str(e):
                    print("!! Erreur: tkinter n'est pas disponible sur ce système.")
                    print("💡 Solutions possibles:")
                    print("   - Sur Windows: Réinstallez Python depuis python.org avec l'option 'tcl/tk and IDLE'")
                    print("   - Ou téléchargez Python depuis Microsoft Store")
                    print("   - Ou utilisez le mode CLI: python ollamaTrad.py")
                    sys.exit(1)
                else:
                    raise

        else:
            # Lancer l'interface en ligne de commande
            print("🚀 Lancement du CLI OllamaTrad...")

            from cli.commands import CLIInterface

            cli = CLIInterface()

            # Charger un fichier au démarrage si spécifié
            if args.file:
                cli.cmd_load(args.file)

            # Exécuter une commande directement ou lancer le mode interactif
            if args.command:
                cli.parse_and_execute(args.command)
            else:
                cli.run_interactive()

    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Conseil: Vérifiez que toutes les dépendances sont installées avec:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()