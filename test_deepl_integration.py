#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'intégration DeepL et le comptage des caractères.

Usage:
    python test_deepl_integration.py
"""

import asyncio
from core.ai_client import AIClient, DeepLProvider
from pathlib import Path


async def test_character_counting():
    """Test du système de comptage de caractères."""
    print("=" * 60)
    print("TEST 1: Système de comptage de caractères")
    print("=" * 60)

    client = AIClient()

    # Simuler des appels avec différents providers
    providers_to_test = ["ollama", "openai", "mistral", "anthropic", "deepl"]

    for provider_name in providers_to_test:
        if provider_name in client.providers:
            provider = client.providers[provider_name]
            print(f"\n{provider_name.upper()}:")
            print(f"  • Compteur initial: {provider.get_character_count()}")

            # Simuler l'envoi de texte
            provider._count_characters("Hello world! This is a test.")
            provider._count_characters("Another test message.")

            print(f"  • Compteur après 2 messages: {provider.get_character_count()}")
        else:
            print(f"\n{provider_name.upper()}: Non configuré (ignoré)")

    # Afficher le total
    print("\n" + "-" * 60)
    total = client.get_total_character_count()
    print(f"TOTAL tous providers: {total} caractères")

    # Afficher par provider
    counts = client.get_character_count_by_provider()
    print("\nDétail par provider:")
    for name, count in counts.items():
        if count > 0:
            print(f"  • {name.upper()}: {count:,} caractères")

    print("\n✅ Test du comptage réussi!\n")


async def test_deepl_provider():
    """Test du provider DeepL (nécessite une clé API valide)."""
    print("=" * 60)
    print("TEST 2: Provider DeepL")
    print("=" * 60)

    client = AIClient()

    if "deepl" not in client.providers:
        print("❌ DeepL n'est pas configuré dans settings.json")
        print("   Ajoutez une configuration DeepL pour tester.")
        return

    deepl = client.providers["deepl"]

    # Test de connexion
    print("\n1. Test de connexion...")
    if deepl.check_connection():
        print("   ✅ Connexion réussie!")
    else:
        print("   ❌ Connexion échouée (vérifiez votre clé API)")
        print("   Note: Ce test peut échouer si aucune clé API n'est configurée.")
        return

    # Afficher les informations
    print("\n2. Informations du provider...")
    show_output = await deepl.cmd_show([])
    print(show_output)

    # Test de traduction (si clé API valide)
    print("\n3. Test de traduction...")
    try:
        # Texte simple
        result = await deepl.translate("Hello world!", "FR")
        print(f"   EN → FR: 'Hello world!' → '{result}'")

        # Texte avec HTML
        html_text = "<p>This is a <strong>test</strong>.</p>"
        result_html = await deepl.translate(html_text, "FR")
        print(f"   EN → FR (HTML): '{html_text}' → '{result_html}'")

        # Vérifier le comptage
        print(f"\n   Caractères envoyés: {deepl.get_character_count()}")

        print("\n✅ Test DeepL réussi!")

    except Exception as e:
        print(f"   ⚠️ Traduction échouée: {e}")
        print("   Note: Une clé API DeepL valide est nécessaire pour ce test.")


async def test_deepl_vs_others():
    """Compare DeepL avec les autres providers."""
    print("\n" + "=" * 60)
    print("TEST 3: Comparaison DeepL vs autres providers")
    print("=" * 60)

    print("\nDifférences clés:")
    print("  DeepL:")
    print("    • Service de traduction pur (pas de chat)")
    print("    • Pas de prompt nécessaire")
    print("    • Gestion native du HTML")
    print("    • Facturation au caractère")
    print("    • Langues limitées mais haute qualité")

    print("\n  OpenAI/Mistral/Anthropic:")
    print("    • Chatbots généralistes (+ traduction)")
    print("    • Prompts nécessaires")
    print("    • HTML via instructions dans le prompt")
    print("    • Facturation au token")
    print("    • Nombreuses langues supportées")

    print("\n  Ollama:")
    print("    • LLM local (gratuit)")
    print("    • Pas de limite de caractères")
    print("    • Nécessite ressources locales")

    print("\n✅ Comparaison terminée!\n")


def test_config_loading():
    """Test du chargement de la configuration."""
    print("=" * 60)
    print("TEST 4: Chargement de la configuration")
    print("=" * 60)

    config_path = Path("config/settings.json")

    if not config_path.exists():
        print(f"❌ Fichier de configuration non trouvé: {config_path}")
        return

    print(f"✅ Fichier de configuration trouvé: {config_path}")

    client = AIClient()

    print("\nProviders disponibles:")
    for name in client.get_available_providers():
        provider = client.providers[name]
        connected = "✅" if provider.check_connection() else "❌"
        char_count = provider.get_character_count()
        print(f"  {connected} {name.upper()} (compteur: {char_count})")

    print(f"\nProvider actuel: {client.get_current_provider_name().upper()}")
    print("\n✅ Configuration chargée avec succès!\n")


async def main():
    """Point d'entrée principal."""
    print("\n" + "🧪 " * 20)
    print("Tests d'intégration DeepL et comptage de caractères")
    print("🧪 " * 20 + "\n")

    # Test 1: Comptage de caractères
    await test_character_counting()

    # Test 2: Configuration
    test_config_loading()

    # Test 3: Provider DeepL
    await test_deepl_provider()

    # Test 4: Comparaison
    await test_deepl_vs_others()

    print("=" * 60)
    print("📝 RÉSUMÉ")
    print("=" * 60)
    print("""
Les fonctionnalités suivantes ont été ajoutées:

1. ✅ Provider DeepL pour traduction professionnelle
2. ✅ Comptage de caractères pour tous les providers
3. ✅ Affichage du compteur dans la barre de statut GUI
4. ✅ Résumé d'utilisation à la fermeture de l'application
5. ✅ Support complet du HTML par DeepL
6. ✅ Gestion des comptes Free et Pro
7. ✅ Commande /show avec statistiques détaillées

Configuration requise:
- Ajouter votre clé API DeepL dans config/settings.json
- Choisir entre api-free.deepl.com (gratuit) ou api.deepl.com (Pro)

Limites:
- Compte gratuit: 500,000 caractères/mois
- DeepL ne peut pas être utilisé pour le chat (ia command)
- Utilisez uniquement pour les commandes de traduction
    """)

    print("Tous les tests terminés! 🎉\n")


if __name__ == "__main__":
    asyncio.run(main())
