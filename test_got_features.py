#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour les fonctionnalités du système .got.json
"""

import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from core.got_json_manager import GotJsonManager


def test_translation_history():
    """Test de la gestion de l'historique des traductions"""
    print("=" * 60)
    print("TEST 1: Gestion de l'historique des traductions")
    print("=" * 60)

    # Charger le fichier .got.json
    manager = GotJsonManager(target_languages=["fr", "es", "de"])
    manager.load_from_file("test_simple.got.json")

    # Tester les mises à jour avec historique
    path = "app/title"
    print(f"\n1. État initial de '{path}':")
    entry = manager._get_entry_by_path(path)
    print(f"   ori: {entry['ori']}")
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")
    print(f"   fr.valid: {entry['fr']['valid']}")

    # Première traduction
    print(f"\n2. Première traduction (fr): 'Mon Application'")
    manager.update_translation(path, "fr", "Mon Application")
    entry = manager._get_entry_by_path(path)
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")
    print(f"   fr.valid: {entry['fr']['valid']}")

    # Amélioration de la traduction
    print(f"\n3. Amélioration de la traduction (fr): 'Mon App'")
    manager.update_translation(path, "fr", "Mon App")
    entry = manager._get_entry_by_path(path)
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")
    print(f"   fr.valid: {entry['fr']['valid']}")

    # Nouvelle amélioration
    print(f"\n4. Nouvelle amélioration (fr): 'Mon Application Pro'")
    manager.update_translation(path, "fr", "Mon Application Pro")
    entry = manager._get_entry_by_path(path)
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")
    print(f"   fr.valid: {entry['fr']['valid']}")

    # Rollback
    print(f"\n5. Rollback vers la version précédente:")
    restored = manager.rollback_translation(path, "fr")
    entry = manager._get_entry_by_path(path)
    print(f"   Texte restauré: '{restored}'")
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")

    # Rollback encore
    print(f"\n6. Rollback encore:")
    restored = manager.rollback_translation(path, "fr")
    entry = manager._get_entry_by_path(path)
    print(f"   Texte restauré: '{restored}'")
    print(f"   fr.text: '{entry['fr']['text']}'")
    print(f"   fr.history: {entry['fr']['history']}")

    print("\n✓ Test de l'historique terminé avec succès!")
    return manager


def test_validation_states(manager):
    """Test des états de validation"""
    print("\n" + "=" * 60)
    print("TEST 2: États de validation")
    print("=" * 60)

    path = "app/title"

    # État initial (aucune traduction validée)
    print(f"\n1. État initial:")
    state = manager.get_validation_state(path)
    print(f"   État de validation: {state}")

    # Valider la traduction française
    print(f"\n2. Validation de la traduction française:")
    manager.validate_translation(path, "fr", True)
    state = manager.get_validation_state(path)
    entry = manager._get_entry_by_path(path)
    print(f"   fr.valid: {entry['fr']['valid']}")
    print(f"   État de validation: {state}")

    # Ajouter une traduction espagnole
    print(f"\n3. Ajout traduction espagnole: 'Mi Aplicación'")
    manager.update_translation(path, "es", "Mi Aplicación")
    state = manager.get_validation_state(path)
    print(f"   État de validation: {state} (partiellement validé)")

    # Valider l'espagnol
    print(f"\n4. Validation de l'espagnol:")
    manager.validate_translation(path, "es", True)
    state = manager.get_validation_state(path)
    print(f"   État de validation: {state} (encore partiel car DE non traduit)")

    # Ajouter et valider l'allemand
    print(f"\n5. Ajout et validation allemand: 'Meine Anwendung'")
    manager.update_translation(path, "de", "Meine Anwendung")
    manager.validate_translation(path, "de", True)
    state = manager.get_validation_state(path)
    print(f"   État de validation: {state} (tout validé)")

    print("\n✓ Test des états de validation terminé avec succès!")


def test_translation_stats(manager):
    """Test des statistiques de traduction"""
    print("\n" + "=" * 60)
    print("TEST 3: Statistiques de traduction")
    print("=" * 60)

    # Ajouter quelques traductions supplémentaires
    print("\n1. Ajout de traductions supplémentaires:")
    manager.update_translation("messages/welcome", "fr", "Bienvenue dans notre application!")
    manager.validate_translation("messages/welcome", "fr", True)

    manager.update_translation("messages/goodbye", "fr", "Merci d'avoir utilisé notre app")
    # Ne pas valider celle-ci

    manager.update_translation("app/settings/theme", "fr", "Mode sombre")
    manager.validate_translation("app/settings/theme", "fr", True)

    # Obtenir les statistiques
    print("\n2. Statistiques globales:")
    stats = manager.get_translation_stats()
    print(f"   Total d'entrées traduisibles: {stats['total_entries']}")

    print(f"\n3. Par langue:")
    for lang in manager.target_languages:
        lang_stats = stats['by_language'][lang]
        print(f"   {lang.upper()}:")
        print(f"     - Traduites: {lang_stats['translated']}/{stats['total_entries']} ({lang_stats['percentage']:.1f}%)")
        print(f"     - Validées: {lang_stats['validated']}")

    print(f"\n4. États de validation:")
    val_stats = stats['validation_states']
    print(f"   - ✅ Toutes validées (green): {val_stats['green']}")
    print(f"   - 🟠 Partiellement (orange): {val_stats['orange']}")
    print(f"   - ❌ Non validées (red): {val_stats['red']}")
    print(f"   - ⚪ Pas de traduction (none): {val_stats['none']}")

    print("\n✓ Test des statistiques terminé avec succès!")


def test_get_all_translatable_paths(manager):
    """Test de la récupération de tous les chemins traduisibles"""
    print("\n" + "=" * 60)
    print("TEST 4: Liste de tous les chemins traduisibles")
    print("=" * 60)

    paths = manager.get_all_translatable_paths()
    print(f"\nNombre total de chemins traduisibles: {len(paths)}")
    print("\nListe des chemins:")
    for i, path in enumerate(paths, 1):
        entry = manager._get_entry_by_path(path)
        ori = entry['ori']
        print(f"  {i:2d}. {path:<35} → \"{ori}\"")

    print("\n✓ Test de récupération des chemins terminé avec succès!")


def main():
    """Fonction principale"""
    print("\n🧪 TESTS DES FONCTIONNALITÉS .got.json\n")

    try:
        # Test 1: Historique
        manager = test_translation_history()

        # Test 2: États de validation
        test_validation_states(manager)

        # Test 3: Statistiques
        test_translation_stats(manager)

        # Test 4: Liste des chemins
        test_get_all_translatable_paths(manager)

        # Sauvegarder le fichier modifié
        output_file = "test_simple_modified.got.json"
        manager.save_to_file(output_file)
        print(f"\n💾 Fichier sauvegardé: {output_file}")

        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS ONT RÉUSSI!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
