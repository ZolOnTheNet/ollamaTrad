#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'interface BatchTranslationForm - Vérification de la visibilité
"""

import tkinter as tk
from tkinter import ttk
import sys
sys.path.insert(0, '.')

from gui.batch_translation_form import BatchTranslationForm

def test_ui():
    root = tk.Tk()
    root.title("Test BatchTranslationForm - Visibilité")
    root.geometry("600x700")

    # Créer le formulaire
    batch_form = BatchTranslationForm(
        root,
        visible_languages=["fr", "en", "es"],
        on_batch_translate=lambda lang: print(f"Traduire en {lang}")
    )
    batch_form.pack(fill="both", expand=True)

    # Charger des données de test
    test_leaves = [
        "entries/Demon/name",
        "entries/Angel/name",
        "entries/Demon/tokenName",
        "entries/Angel/tokenName",
        "entries/Demon/description",
        "entries/Angel/description",
        "entries/Beast/name",
        "entries/Beast/tokenName",
        "settings/title",
    ]

    batch_form.load_branch("entries", test_leaves)

    # Boutons de test pour simuler le processus
    test_frame = ttk.Frame(root)
    test_frame.pack(fill="x", pady=10)

    def start_test():
        """Simule le démarrage du traitement"""
        print("🟢 Démarrage du traitement (config cachée, progress visible)")
        batch_form.start_processing(5)

    def update_test():
        """Simule une mise à jour de progression"""
        print("🔵 Mise à jour progression")
        batch_form.update_progress(3, 5, "entries/Demon/name")

    def finish_test():
        """Simule la fin du traitement"""
        print("🟢 Fin du traitement (config visible, progress cachée)")
        batch_form.finish_processing(success=True)

    def stop_test():
        """Simule un arrêt"""
        print("🟡 Arrêt du traitement")
        batch_form.finish_processing(success=False)

    ttk.Label(test_frame, text="Tests de visibilité:", font=("Arial", 10, "bold")).pack(pady=5)
    ttk.Button(test_frame, text="1️⃣ Démarrer traitement", command=start_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="2️⃣ Mettre à jour (3/5)", command=update_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="3️⃣ Terminer (succès)", command=finish_test).pack(side="left", padx=5)
    ttk.Button(test_frame, text="4️⃣ Terminer (arrêt)", command=stop_test).pack(side="left", padx=5)

    print("Interface créée. Testez les boutons pour vérifier la visibilité.")
    print("- Au départ: config visible, progress cachée")
    print("- Après 'Démarrer': config cachée, progress visible")
    print("- Après 'Terminer': config visible, progress cachée (après 3s)")

    root.mainloop()

if __name__ == "__main__":
    test_ui()
