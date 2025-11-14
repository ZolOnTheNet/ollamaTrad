# Fonctionnalité : Export vers JSON

## Description

OllamaFic permet d'exporter un fichier .got.json vers un fichier JSON standard, en utilisant les traductions d'une langue spécifique. Deux modes d'export sont disponibles selon vos besoins de qualité.

## Accès

**Menu Fichier → 📤 Exporter vers JSON...**

Le menu affiche automatiquement toutes les langues cibles disponibles dans le fichier .got.json actuel.

### Menu dynamique

```
Fichier
├── Ouvrir JSON/GOT...
├── Sauvegarder
├── ───────────────────
├── 📤 Exporter vers JSON...
│   ├── FR
│   ├── EN
│   ├── ES
│   ├── ───────────
│   └── Autre...
├── ───────────────────
├── ⚙️ Options...
└── Quitter
```

## Dialogue d'export

### Configuration

Le dialogue d'export permet de configurer tous les paramètres :

```
┌─────────────────────────────────────────────────┐
│ 📤 Export vers JSON                             │
├─────────────────────────────────────────────────┤
│                                                 │
│ ╔═══════════════════════════════════════════╗  │
│ ║ Langue cible                              ║  │
│ ╚═══════════════════════════════════════════╝  │
│   Langue: [FR ▼]                                │
│                                                 │
│ ╔═══════════════════════════════════════════╗  │
│ ║ Fichier de destination                    ║  │
│ ╚═══════════════════════════════════════════╝  │
│   Répertoire: [/path/to/files] [Parcourir...] │
│   Nom:        [messages-fr.json            ]  │
│                                                 │
│ ╔═══════════════════════════════════════════╗  │
│ ║ Mode d'export                             ║  │
│ ╚═══════════════════════════════════════════╝  │
│   ○ Standard                                    │
│      ℹ️ Export identique au JSON original,     │
│         avec traduction prioritaire si définie  │
│                                                 │
│   ● Unique Validé                              │
│      ℹ️ N'exporte que les traductions          │
│         validées et non vides, sinon l'original │
│                                                 │
│                        [Annuler] [Exporter]     │
└─────────────────────────────────────────────────┘
```

### Champs

#### 1. Langue cible

Sélectionne la langue à exporter dans le JSON.

- **Pré-rempli** si vous avez cliqué sur une langue spécifique dans le menu
- **Liste complète** des langues cibles configurées
- Détermine quelle traduction sera utilisée

#### 2. Répertoire de destination

Choisit où sauvegarder le fichier exporté.

- **Par défaut** : Même répertoire que le fichier .got.json
- **Bouton Parcourir** : Ouvre un sélecteur de dossier

#### 3. Nom de fichier

Nom du fichier JSON de sortie.

- **Format par défaut** : `{nom-original}-{langue}.json`
- **Exemples** :
  - `messages.json` → `messages-fr.json`
  - `app.got.json` → `app-en.json`
- **Éditable** : Vous pouvez choisir n'importe quel nom

#### 4. Mode d'export

Deux modes disponibles, chacun avec un tooltip explicatif.

## Modes d'export

### Mode "Standard"

**Principe** : Utilise la traduction si elle existe et n'est pas vide, sinon conserve l'original.

#### Règle

```
Pour chaque champ traduisible:
  SI traduction[langue].text est définie ET non vide:
    → Utiliser traduction[langue].text
  SINON:
    → Utiliser ori (original)
```

#### Exemple

**Données .got.json** :

```json
{
  "__ollamafic__": {...},
  "title": {
    "ori": "Hello World",
    "fr": {"text": "Bonjour le monde", "valid": true}
  },
  "subtitle": {
    "ori": "Welcome",
    "fr": {"text": "", "valid": false}
  },
  "footer": {
    "ori": "Goodbye",
    "fr": {"text": "Au revoir", "valid": false}
  }
}
```

**Export FR en mode Standard** :

```json
{
  "title": "Bonjour le monde",    ← Traduit (non vide)
  "subtitle": "Welcome",          ← Original (traduction vide)
  "footer": "Au revoir"           ← Traduit (non vide même si non validé)
}
```

#### Cas d'usage

- **Export de travail** : Voir toutes les traductions en cours
- **Preview** : Tester l'application avec traductions partielles
- **Développement** : Utiliser toutes les traductions disponibles

### Mode "Unique Validé"

**Principe** : Utilise UNIQUEMENT les traductions validées et non vides, sinon conserve l'original.

#### Règle

```
Pour chaque champ traduisible:
  SI traduction[langue].text est définie ET non vide ET valid == true:
    → Utiliser traduction[langue].text
  SINON:
    → Utiliser ori (original)
```

#### Exemple

**Données .got.json** (même que ci-dessus) :

```json
{
  "__ollamafic__": {...},
  "title": {
    "ori": "Hello World",
    "fr": {"text": "Bonjour le monde", "valid": true}
  },
  "subtitle": {
    "ori": "Welcome",
    "fr": {"text": "", "valid": false}
  },
  "footer": {
    "ori": "Goodbye",
    "fr": {"text": "Au revoir", "valid": false}
  }
}
```

**Export FR en mode Unique Validé** :

```json
{
  "title": "Bonjour le monde",    ← Traduit ET validé ✓
  "subtitle": "Welcome",          ← Original (traduction vide)
  "footer": "Goodbye"             ← Original (traduction NON validée ✗)
}
```

#### Cas d'usage

- **Production** : Export final avec qualité garantie
- **Livraison client** : Seulement les traductions vérifiées
- **Release** : Version stable avec traductions approuvées

## Statistiques avant export

Avant d'exporter, OllamaFic affiche les statistiques pour validation :

```
┌─────────────────────────────────────────────┐
│ Confirmer l'export                          │
├─────────────────────────────────────────────┤
│ Export en mode Standard                     │
│                                             │
│ Langue: FR                                  │
│ Fichier: messages-fr.json                   │
│                                             │
│ Statistiques:                               │
│   • Total d'entrées: 150                    │
│   • Traductions utilisées: 142              │
│   • Originaux conservés: 8                  │
│   • Taux de traduction: 94.7%               │
│                                             │
│ Continuer l'export ?                        │
│                                             │
│                        [Non] [Oui]          │
└─────────────────────────────────────────────┘
```

### Interprétation

- **Total d'entrées** : Nombre total de champs traduisibles
- **Traductions utilisées** : Nombre de champs où la traduction sera utilisée
- **Originaux conservés** : Nombre de champs où l'original sera conservé
- **Taux de traduction** : Pourcentage de traductions utilisées

## Confirmation finale

Après un export réussi :

```
┌─────────────────────────────────────────────┐
│ Export réussi                               │
├─────────────────────────────────────────────┤
│ Le fichier a été exporté avec succès !      │
│                                             │
│ Fichier: /path/to/messages-fr.json          │
│ Langue: FR                                  │
│ Mode: Standard                              │
│ Entrées traduites: 142/150                  │
│                                             │
│                              [OK]            │
└─────────────────────────────────────────────┘
```

## Exemples d'utilisation

### Exemple 1 : Export pour production

**Objectif** : Créer un fichier FR prêt pour la production, avec uniquement les traductions vérifiées.

**Étapes** :
1. Menu **Fichier → Exporter vers JSON... → FR**
2. Sélectionner le répertoire de production
3. Nom : `app-fr.json`
4. Mode : **Unique Validé** ●
5. Vérifier les statistiques (taux de traduction)
6. Confirmer

**Résultat** : Fichier JSON avec 100% de traductions validées.

### Exemple 2 : Export pour test

**Objectif** : Tester l'application avec toutes les traductions disponibles.

**Étapes** :
1. Menu **Fichier → Exporter vers JSON... → FR**
2. Répertoire : Dossier de test
3. Nom : `app-fr-test.json`
4. Mode : **Standard** ○
5. Confirmer sans vérifier les stats

**Résultat** : Fichier JSON avec toutes les traductions, même non validées.

### Exemple 3 : Export multilingue

**Objectif** : Exporter tous les fichiers de langues.

**Étapes** :
1. **Fichier → Exporter vers JSON... → FR**
   - Mode : Unique Validé
   - Fichier : `app-fr.json`

2. **Fichier → Exporter vers JSON... → EN**
   - Mode : Unique Validé
   - Fichier : `app-en.json`

3. **Fichier → Exporter vers JSON... → ES**
   - Mode : Unique Validé
   - Fichier : `app-es.json`

**Résultat** : 3 fichiers JSON, un par langue, tous en mode validé.

### Exemple 4 : Export avec langue personnalisée

**Objectif** : Exporter une langue qui n'est pas dans les cibles habituelles.

**Étapes** :
1. Menu **Fichier → Exporter vers JSON... → Autre...**
2. Dans le dialogue, sélectionner la langue dans la liste complète
3. Configurer et exporter

**Résultat** : Export avec n'importe quelle langue disponible.

## Comparaison des modes

### Scénario : 100 entrées

| Entrées | Standard | Unique Validé |
|---------|----------|---------------|
| 80 traduites et validées | ✅ Traduit | ✅ Traduit |
| 10 traduites mais non validées | ✅ Traduit | ❌ Original |
| 10 non traduites (vides) | ❌ Original | ❌ Original |
| **Résultat** | **90 traductions** | **80 traductions** |
| **Taux** | **90%** | **80%** |

### Choix du mode

| Situation | Mode recommandé |
|-----------|-----------------|
| 🚀 Production / Release | **Unique Validé** |
| 🧪 Test / Preview | **Standard** |
| 👥 Livraison client | **Unique Validé** |
| 🔧 Développement | **Standard** |
| 📦 Version beta | **Standard** |
| 📘 Documentation finale | **Unique Validé** |

## Gestion des erreurs

### Erreur : Langue non disponible

```
❌ Erreur de configuration:
Langue 'de' non disponible. Langues: ['fr', 'en', 'es']
```

**Cause** : La langue sélectionnée n'est pas dans les langues cibles du fichier.

**Solution** : Ajouter la langue dans Options → Langues cibles.

### Erreur : Fichier existant

```
┌─────────────────────────────────────────────┐
│ Fichier existant                            │
├─────────────────────────────────────────────┤
│ Le fichier 'app-fr.json' existe déjà.       │
│                                             │
│ Voulez-vous le remplacer ?                  │
│                                             │
│                        [Non] [Oui]          │
└─────────────────────────────────────────────┘
```

**Choix** :
- **Oui** : Écrase le fichier existant
- **Non** : Retour au dialogue pour changer le nom

### Erreur : Aucun fichier chargé

```
❌ Erreur
Aucun fichier chargé
```

**Solution** : Ouvrir un fichier .got.json avant d'exporter.

## Architecture technique

### Flux d'export

```
┌────────────────────────────────────────────────────────┐
│ 1. Utilisateur : Menu Fichier → Exporter → FR         │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 2. app_v2._export_with_language("fr")                 │
│    - Crée ExportDialog avec langue pré-sélectionnée   │
│    - Affiche le dialogue modal                        │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 3. ExportDialog.show()                                 │
│    - Utilisateur configure :                           │
│      * Langue (pré-remplie : "fr")                     │
│      * Répertoire                                      │
│      * Nom de fichier (auto : "app-fr.json")           │
│      * Mode (standard / validated)                     │
│    - Retourne config ou None si annulé                 │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 4. app_v2._perform_export()                            │
│    - Calcule statistiques (get_export_stats)           │
│    - Affiche dialogue de confirmation                  │
│    - Si confirmé : appelle got_manager.export_to_json()│
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 5. GotJsonManager.export_to_json()                     │
│    - Valide la langue                                  │
│    - Transforme récursivement (_export_transform)      │
│    - Sauvegarde en JSON standard                       │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 6. Transformation de données                           │
│                                                        │
│   .got.json:                  JSON:                    │
│   {                           {                        │
│     "title": {                  "title": "Bonjour",    │
│       "ori": "Hello",           "description": "..."   │
│       "fr": {                 }                        │
│         "text": "Bonjour",                             │
│         "valid": true                                  │
│       }                                                │
│     },                                                 │
│     "description": {...}                               │
│   }                                                    │
└────────────────────────────────────────────────────────┘
```

### Méthodes clés

#### app_v2.py

```python
def _update_export_menu():
    """Crée le menu dynamique avec les langues"""
    for lang in got_manager.target_languages:
        export_menu.add_command(label=lang.upper(), ...)

def _export_with_language(language):
    """Ouvre le dialogue d'export"""
    dialog = ExportDialog(...)
    result = dialog.show()
    if result:
        _perform_export(...)

def _perform_export(output_path, target_language, mode):
    """Effectue l'export avec confirmation"""
    stats = got_manager.get_export_stats(...)
    # Confirmation
    got_manager.export_to_json(...)
```

#### got_json_manager.py

```python
def export_to_json(output_path, target_language, mode):
    """Export principal"""
    exported_data = _export_transform(data, target_language, mode)
    # Sauvegarder en JSON

def _export_transform(value, target_language, mode):
    """Transformation récursive"""
    if is_translation_object(value):
        return _export_translation_object(...)
    # Traiter dicts, lists, etc.

def _export_translation_object(obj, target_language, mode):
    """Logique de sélection traduction/original"""
    if mode == "validated":
        return text if (valid and not_empty) else ori
    else:  # standard
        return text if not_empty else ori

def get_export_stats(target_language, mode):
    """Calcule les statistiques"""
    # Parcourt toutes les entrées
    # Compte translated_entries vs original_entries
```

## Fichiers modifiés

### Nouveaux fichiers

- **gui/export_dialog.py** : Dialogue d'export complet
  - Configuration de tous les paramètres
  - Tooltips explicatifs
  - Validation des entrées

### Fichiers modifiés

- **core/got_json_manager.py** :
  - `export_to_json()` : Export principal
  - `_export_transform()` : Transformation récursive
  - `_export_translation_object()` : Logique traduction/original
  - `get_export_stats()` : Calcul des statistiques

- **gui/app_v2.py** :
  - Menu export dynamique dans `_create_menu()`
  - `_update_export_menu()` : Mise à jour selon langues disponibles
  - `_export_with_language()` : Ouverture dialogue
  - `_perform_export()` : Exécution avec confirmation

## Améliorations futures

### 1. Export batch

Exporter toutes les langues en une seule opération :

```python
def export_all_languages(output_dir, mode):
    """Exporte toutes les langues"""
    for lang in target_languages:
        output_path = f"{output_dir}/app-{lang}.json"
        export_to_json(output_path, lang, mode)
```

### 2. Templates de noms

Configurer le format des noms de fichiers :

```
Options → Export :
  Template: [{name}]-[{lang}].json

Résultat: app-fr.json, app-en.json, ...
```

### 3. Filtres d'export

Exporter seulement certaines sections :

```
Export avancé:
  □ app/*
  ☑ entries/monsters/*
  □ entries/spells/*
```

### 4. Hooks post-export

Exécuter des actions après export :

```
Post-export:
  ☑ Valider JSON
  ☑ Formater avec prettier
  □ Copier vers serveur
```

Cette fonctionnalité d'export rend OllamaFic complet pour tout le workflow de traduction, du travail initial à la production finale !
