#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'interface à onglets BatchTranslationForm
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
sys.path.insert(0, '.')

from gui.batch_translation_form import BatchTranslationForm


def test_tabbed_ui():
    root = tk.Tk()
    root.title("Test BatchTranslationForm - Système d'onglets")
    root.geometry("700x800")

    # Callbacks pour les différentes opérations
    def on_translate(lang, selected_paths):
        print(f"\n🔄 TRADUCTION vers {lang.upper()}")
        print(f"   Chemins sélectionnés: {len(selected_paths)}")
        for path in selected_paths[:5]:  # Afficher seulement les 5 premiers
            print(f"   - {path}")
        if len(selected_paths) > 5:
            print(f"   ... et {len(selected_paths) - 5} autres")
        messagebox.showinfo("Traduction",
                          f"Traduction de {len(selected_paths)} champ(s) vers {lang.upper()}")

    def on_search_replace(search, replace, selected_paths, options):
        print(f"\n🔍 RECHERCHER & REMPLACER")
        print(f"   Rechercher: '{search}'")
        print(f"   Remplacer par: '{replace}'")
        print(f"   Options: {options}")
        print(f"   Chemins sélectionnés: {len(selected_paths)}")
        for path in selected_paths[:5]:
            print(f"   - {path}")
        if len(selected_paths) > 5:
            print(f"   ... et {len(selected_paths) - 5} autres")
        messagebox.showinfo("Rechercher & Remplacer",
                          f"Remplacement dans {len(selected_paths)} champ(s)\n"
                          f"'{search}' → '{replace}'")

    def on_undo(selected_paths, mode):
        print(f"\n↶ ANNULER MODIFICATIONS")
        print(f"   Mode: {mode}")
        print(f"   Chemins sélectionnés: {len(selected_paths)}")
        for path in selected_paths[:5]:
            print(f"   - {path}")
        if len(selected_paths) > 5:
            print(f"   ... et {len(selected_paths) - 5} autres")
        messagebox.showinfo("Annuler",
                          f"Annulation de {len(selected_paths)} champ(s)\n"
                          f"Mode: {mode}")

    # Créer le formulaire
    batch_form = BatchTranslationForm(
        root,
        visible_languages=["fr", "en", "es", "de"],
        on_batch_translate=on_translate,
        on_search_replace=on_search_replace,
        on_undo=on_undo
    )
    batch_form.pack(fill="both", expand=True)

    # Charger des données de test
    test_leaves = [
        "entries/Demon/name",
        "entries/Angel/name",
        "entries/Beast/name",
        "entries/Demon/tokenName",
        "entries/Angel/tokenName",
        "entries/Beast/tokenName",
        "entries/Demon/description",
        "entries/Angel/description",
        "entries/Beast/description",
        "settings/app/title",
        "settings/app/subtitle",
        "settings/config/language",
        "settings/config/theme",
    ]

    batch_form.load_branch("entries", test_leaves)

    # Boutons de test pour simuler le processus
    test_frame = ttk.LabelFrame(root, text="Tests de progression", padding=10)
    test_frame.pack(fill="x", pady=10, padx=10)

    def start_test():
        """Simule le démarrage du traitement"""
        print("\n🟢 DÉMARRAGE du traitement")
        batch_form.start_processing(5)

    def update_test():
        """Simule une mise à jour de progression"""
        print("🔵 MISE À JOUR progression (3/5)")
        batch_form.update_progress(3, 5, "entries/Demon/name")

    def finish_success_test():
        """Simule la fin du traitement"""
        print("🟢 FIN du traitement (succès)")
        batch_form.finish_processing(success=True)

    def finish_stop_test():
        """Simule un arrêt"""
        print("🟡 ARRÊT du traitement")
        batch_form.finish_processing(success=False)

    ttk.Button(test_frame, text="1️⃣ Démarrer", command=start_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="2️⃣ Maj (3/5)", command=update_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="3️⃣ Terminer ✓", command=finish_success_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="4️⃣ Arrêter ⏹", command=finish_stop_test).pack(side="left", padx=5)

    # Instructions
    info_frame = ttk.Frame(root)
    info_frame.pack(fill="x", pady=5, padx=10)

    instructions = """
    📌 Instructions:
    1. Testez les 3 onglets (Traduction, Rechercher & Remplacer, Annuler)
    2. Sélectionnez/désélectionnez des champs
    3. Cliquez sur les boutons d'action de chaque onglet
    4. Testez la progression avec les boutons de test
    """

    ttk.Label(info_frame, text=instructions, font=("Arial", 8),
             foreground="gray", justify="left").pack(anchor="w")

    print("=" * 70)
    print("INTERFACE CRÉÉE - Testez les onglets!")
    print("=" * 70)

    root.mainloop()


if __name__ == "__main__":
    test_tabbed_ui()
