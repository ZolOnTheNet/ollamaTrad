# Changelog - Intégration DeepL et Comptage de Caractères

## Version 2.1.0 - Nouvelle fonctionnalité : DeepL et comptage

### 🎯 Nouvelles fonctionnalités

#### 1. Provider DeepL
- ✅ **Nouveau provider de traduction professionnel** : Support complet de l'API DeepL
- ✅ **Traduction haute qualité** : Reconnue pour sa qualité supérieure aux LLMs généralistes
- ✅ **Gestion native du HTML** : Préservation automatique des balises sans prompt
- ✅ **Comptes Free et Pro** : Support des deux types de comptes
- ✅ **Interface simplifiée** : Pas de prompt nécessaire, juste langue source → cible

#### 2. Système de comptage de caractères
- ✅ **Compteur par provider** : Suivi individuel pour chaque API payante
- ✅ **Affichage en temps réel** : Compteur dans la barre de statut (GUI)
- ✅ **Résumé à la fermeture** : Boîte de dialogue avec statistiques complètes
- ✅ **Estimation des coûts** : Calcul approximatif du coût pour chaque provider
- ✅ **Quota DeepL** : Affichage du quota utilisé / limite mensuelle

#### 3. Interface graphique améliorée
- ✅ **Barre de statut enrichie** : Affichage du compteur de caractères
- ✅ **Mise à jour automatique** : Rafraîchissement toutes les 2 secondes
- ✅ **Dialogue de fermeture** : Résumé automatique avant sortie
- ✅ **Support multi-provider** : Comptage consolidé pour tous les providers payants

### 🔧 Modifications techniques

#### Fichiers modifiés

**`core/ai_client.py`**
- Ajout de la classe `DeepLProvider`
- Ajout de `character_count` dans `AIProvider` (classe de base)
- Nouvelles méthodes :
  - `get_character_count()` : Retourne le compteur
  - `reset_character_count()` : Remet à zéro
  - `_count_characters(text)` : Incrémente le compteur
  - `get_total_character_count()` : Total tous providers
  - `get_character_count_by_provider()` : Dict par provider
- Ajout du comptage dans les méthodes `chat()` de :
  - `OpenAIProvider`
  - `MistralProvider`
  - `AnthropicProvider`
- Initialisation de `DeepLProvider` dans `AIClient.init_providers()`

**`config/settings.json`**
- Nouvelle section `"deepl"` :
  ```json
  {
    "api_url": "https://api-free.deepl.com/v2/translate",
    "api_key": "",
    "is_pro": false,
    "timeout": 30,
    "available_languages": [...]
  }
  ```

**`gui/app_v2.py`**
- Ajout du label `char_count_label` dans la barre de statut
- Nouvelle méthode `_update_character_count()` : Mise à jour périodique
- Nouvelle méthode `_show_character_usage_summary()` : Dialogue de fermeture
- Modification de `run()` : Interception de la fermeture (`WM_DELETE_WINDOW`)

#### Nouveaux fichiers

**`DEEPL_INTEGRATION.md`**
- Documentation complète de l'intégration DeepL
- Guide de configuration Free/Pro
- Comparaison avec autres providers
- Exemples d'utilisation
- Dépannage et FAQ

**`QUICKSTART_DEEPL.md`**
- Guide de démarrage rapide (5 minutes)
- Configuration minimale
- Cas d'usage typiques
- Astuces et optimisation des coûts

**`test_deepl_integration.py`**
- Script de test complet
- Vérification du comptage de caractères
- Test de connexion DeepL
- Comparaison des providers

**`CHANGELOG_DEEPL.md`**
- Ce fichier

### 📊 Providers supportés avec comptage

| Provider | Type | Comptage | Estimation coût |
|----------|------|----------|-----------------|
| Ollama | Local | ❌ Non | Gratuit |
| OpenAI | API | ✅ Oui | ~$0.03/1K tokens |
| Mistral | API | ✅ Oui | ~$0.002/1K tokens |
| Anthropic | API | ✅ Oui | ~$0.015/1K tokens |
| DeepL | API | ✅ Oui | €20/1M chars (Pro) |

### 🎨 Interface utilisateur

#### Avant
```
[Status: Prêt] [Fichier: data.json]
```

#### Après
```
[Status: Prêt] [📊 1,245 car.] [Fichier: data.json]
```

#### Dialogue de fermeture (nouveau)
```
📊 Résumé de l'utilisation durant cette session:

  • DEEPL: 15,420 caractères
  • OPENAI: 5,230 caractères

  Total: 20,650 caractères

💰 Estimation de coût approximative:
  • OpenAI: ~$0.0392
  • DeepL: 15,420 / 500,000 chars gratuits

ℹ️ Ces estimations sont approximatives.
```

### 🔄 Compatibilité

- ✅ **Rétrocompatible** : Pas de changement pour les utilisateurs actuels
- ✅ **Configuration optionnelle** : DeepL peut être ignoré si non configuré
- ✅ **Pas de dépendances** : Utilise les bibliothèques existantes (aiohttp, requests)
- ✅ **Migration transparente** : Les anciens fichiers settings.json restent valides

### 📝 Notes de migration

#### Pour les utilisateurs existants
1. Aucune action requise si vous n'utilisez pas DeepL
2. Le compteur de caractères fonctionne automatiquement pour tous les providers payants
3. Les settings.json existants sont automatiquement complétés

#### Pour activer DeepL
1. Ajoutez la section `"deepl"` dans `config/settings.json`
2. Obtenez une clé API sur https://www.deepl.com/pro-api
3. Configurez dans l'interface **Options** → **Providers** → **DeepL**

### 🐛 Problèmes connus

1. **Tooltip non natif** : Le compteur de caractères n'a pas de tooltip hover (limitation tkinter standard)
2. **Délai de mise à jour** : Le compteur se rafraîchit toutes les 2 secondes (pas instantané)
3. **DeepL chat** : La méthode `chat()` de DeepL lève une exception (comportement attendu)

### 🔮 Améliorations futures

- [ ] Graphique d'évolution du compteur
- [ ] Export des statistiques en CSV
- [ ] Alertes de quota (seuil configurable)
- [ ] Historique d'utilisation par jour/semaine/mois
- [ ] Support des tooltips avec bibliothèque tierce
- [ ] Estimation en temps réel avant envoi

### 📖 Documentation

- Guide complet : `DEEPL_INTEGRATION.md`
- Démarrage rapide : `QUICKSTART_DEEPL.md`
- Tests : `test_deepl_integration.py`
- Architecture : `CLAUDE.md` (mis à jour)

### 👥 Contributeurs

- Implémentation initiale : Claude Code
- Tests et validation : [Votre nom]

### 📅 Dates

- **Début développement** : 2025-11-07
- **Première version** : 2025-11-07
- **Version stable** : 2.1.0

---

## Comment utiliser

### Configuration minimale

```json
{
  "ai_providers": {
    "deepl": {
      "api_key": "votre-clé-api",
      "is_pro": false
    }
  }
}
```

### Commandes de base

```bash
# Activer DeepL
provider set deepl

# Traduire
translate -fr mon/chemin

# Vérifier l'utilisation
/show

# Résultat :
# 📊 Caractères envoyés: 1,245
# 📈 Utilisation API: 1,245 / 500,000 (0.2%)
```

### Interface graphique

1. **Fichier** → **Options** → **Providers** → **DeepL**
2. Configurez votre clé API
3. Utilisez normalement
4. Consultez le compteur en bas à droite : `📊 1,245 car.`
5. À la fermeture, voyez le résumé complet

---

**Merci d'utiliser OllamaFic ! 🎉**
