# Changelog - OllamaTrad

## [Refactorisation majeure] - 2025-01-14

### 🎉 Renommage du projet
- **OllamaFic** → **OllamaTrad**
- Nom cohérent dans tout le code et la documentation

### 🧹 Nettoyage du code
- Suppression de 47 000+ lignes de code obsolète
- Suppression de 30+ fichiers de documentation temporaire (BUGFIX_*, FEATURE_*)
- Suppression des modules legacy :
  - `core/json_manager.py`
  - `core/metadata.py`
  - `core/ollama_client.py`
  - `core/operation_history.py`
  - `core/instructions.py`
- Suppression des fichiers de test temporaires

### 📝 Renommage des fichiers
- `gui/app_v2.py` → `gui/app.py`
- `gui/options_dialog_v3.py` → `gui/options_dialog.py`
- `gui/translation_form_v2.py` → `gui/translation_form.py`
- Plus de versionnage dans les noms de fichiers

### 📚 Nouvelle documentation
- **README.md** complet avec guide d'installation et d'utilisation
- **CHANGELOG.md** pour suivre l'évolution du projet

### ✨ Fonctionnalités récentes

#### Protection des champs validés
- Les champs marqués comme validés (`valid: true`) ne sont plus retraduits lors des traitements par lot
- Protection absolue contre la retraduction accidentelle

#### Message de confirmation à la fermeture
- Dialogue Oui/Non/Annuler si des modifications non sauvegardées existent
- Option "Sauvegarde automatique" dans Options → Avancé
- Indicateur visuel `*` dans le titre de la fenêtre

#### Compteur DeepL amélioré
- Calcul précis du nombre de caractères qui seront traduits
- Exclusion des champs validés et déjà traduits
- Compteur spécifique par langue

## [Version précédente] - 2024

### Fonctionnalités principales
- Interface graphique modernisée avec formulaire de traduction
- Support multi-providers IA (Ollama, OpenAI, Mistral, Anthropic, DeepL)
- Format .got.json v2.0 avec historique et validation
- Traduction par lot avec sélection de champs
- Chat contextuel avec l'IA
- Code couleur de l'arbre JSON par état de validation
- Amélioration IA (baguette magique)
- Détection et préservation du HTML
- Traduction partielle (garder une partie de la traduction IA)
