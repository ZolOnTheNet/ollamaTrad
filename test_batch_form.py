#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide pour vérifier la logique du BatchTranslationForm
"""

# Simuler la logique de groupement et de sélection
def test_logic():
    # Simulation de feuilles
    leaves = [
        "entries/Demon/name",
        "entries/Angel/name",
        "entries/Demon/tokenName",
        "entries/Angel/tokenName",
        "entries/Demon/description",
        "settings/title/name",
    ]

    # Grouper par nom de champ final
    field_to_paths = {}
    for leaf_path in leaves:
        field_name = leaf_path.split("/")[-1]
        if field_name not in field_to_paths:
            field_to_paths[field_name] = []
        field_to_paths[field_name].append(leaf_path)

    print("Groupement des champs:")
    for field_name, paths in sorted(field_to_paths.items()):
        print(f"  {field_name} ({len(paths)}×): {paths}")

    # Simulation de checkboxes
    field_checkboxes = {
        "name": True,  # Coché
        "tokenName": False,  # Décoché
        "description": True,  # Coché
    }

    print("\nÉtat des checkboxes:")
    for field_name, checked in sorted(field_checkboxes.items()):
        status = "✓" if checked else "☐"
        print(f"  {status} {field_name}")

    # Simulation de get_selected_leaves()
    selected = []
    for field_name, checked in field_checkboxes.items():
        if checked:
            selected.extend(field_to_paths[field_name])

    print("\nFeuilles sélectionnées pour traduction:")
    for path in selected:
        print(f"  - {path}")

    print("\nFeuilles NON sélectionnées (ne seront pas traduites):")
    all_selected = set(selected)
    for leaf in leaves:
        if leaf not in all_selected:
            print(f"  - {leaf}")

if __name__ == "__main__":
    test_logic()
