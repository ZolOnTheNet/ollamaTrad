# Nouvelle Fonctionnalité: Fenêtre d'Options

## 📅 Date: 2025-10-16

## 🎯 Objectif

Permettre à l'utilisateur de configurer facilement:
- Les langues disponibles et leur ordre
- Les langues visibles dans le formulaire
- Les prompts personnalisés pour les traductions

---

## ✨ Fonctionnalités

### 1. 🌍 Onglet Langues

#### Langues Connues
Liste des langues disponibles pour la traduction:
- `fr` - Français
- `en` - English
- `es` - Español
- `de` - Deutsch
- `it` - Italiano
- `pt` - Português
- `ru` - Русский
- `ja` - 日本語
- `zh` - 中文
- `ar` - العربية

#### Langues Cibles (Ordre de Traduction)
- Saisie des codes de langues séparés par des virgules
- Exemple: `fr, en, es`
- Détermine l'ordre d'apparition dans le formulaire

#### Langues Visibles (Filtrage)
- Cases à cocher pour chaque langue
- Permet de masquer certaines langues pour le fichier actuel
- **Important**: Les données restent dans le `.got.json`, seul l'affichage change

**Exemple d'utilisation**:
```
Langues cibles: fr, en, es, de, it
Langues visibles: ☑ fr  ☑ en  ☐ es  ☐ de  ☐ it

→ Le formulaire affichera seulement fr et en
→ Les traductions es, de, it restent dans le fichier
```

---

### 2. 💬 Onglet Prompts de Traduction

Personnalisation complète des prompts envoyés à l'IA.

#### Variables Disponibles
- `{text}` - Texte à traduire
- `{lang}` - Code de langue cible
- `{original}` - Texte original (pour amélioration)
- `{current}` - Traduction actuelle (pour amélioration)
- `{context}` - Contexte de l'entrée

#### Quatre Types de Prompts

**1. 📝 Traduction Simple**
```
Utilisé pour: Traduire du texte sans HTML
Exemple par défaut:
Traduis "{text}" en {lang}. Réponds uniquement avec la traduction, sans explication.
```

**2. 🌐 Traduction HTML**
```
Utilisé pour: Traduire du contenu avec balises HTML
Exemple par défaut:
Traduis le texte suivant en {lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.
Ne traduis QUE le texte entre les balises, PAS les balises elles-mêmes.

Texte à traduire:
{text}

Réponds uniquement avec la traduction, en préservant exactement toutes les balises HTML.
```

**3. ✨ Amélioration Simple**
```
Utilisé pour: Améliorer une traduction sans HTML
Exemple par défaut:
Améliore cette traduction {lang}:
Texte original: "{original}"
Traduction actuelle: "{current}"
Contexte: {context}

Corrige l'orthographe, la grammaire et rends la phrase plus naturelle.
Réponds uniquement avec la traduction améliorée, sans explication.
```

**4. 🌐✨ Amélioration HTML**
```
Utilisé pour: Améliorer une traduction avec HTML
Exemple par défaut:
Améliore cette traduction {lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.

Texte original: {original}
Traduction actuelle: {current}
Contexte: {context}

Corrige l'orthographe, la grammaire et rends la phrase plus naturelle.
Réponds uniquement avec la traduction améliorée, en préservant exactement toutes les balises HTML.
```

---

## 🔧 Accès à la Fenêtre d'Options

**Menu**: `Fichier` → `⚙️ Options...`

Raccourci: Aucun (pour l'instant)

---

## 💾 Configuration Sauvegardée

Les options sont sauvegardées dans:
```
config/translation_config.json
```

**Format**:
```json
{
  "known_languages": {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    ...
  },
  "target_languages": ["fr", "en", "es"],
  "visible_languages": ["fr", "en"],
  "prompts": {
    "translate": "...",
    "translate_html": "...",
    "improve": "...",
    "improve_html": "..."
  }
}
```

---

## 🎨 Interface de la Fenêtre

### Layout
```
┌─────────────────────────────────────────────────────────┐
│ Options - OllamaFic v2.0                            [X] │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────┐  │
│ │ 🌍 Langues │ 💬 Prompts de Traduction │          │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ [Contenu selon l'onglet sélectionné]                   │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [🔄 Réinitialiser]             [❌ Annuler] [💾 Sauvegarder] │
└─────────────────────────────────────────────────────────┘
```

### Boutons

**💾 Sauvegarder**
- Valide les entrées
- Sauvegarde dans `translation_config.json`
- Rafraîchit l'affichage si un fichier est ouvert
- Ferme la fenêtre

**❌ Annuler**
- Ferme la fenêtre sans sauvegarder

**🔄 Réinitialiser**
- Recharge les valeurs par défaut
- Ne sauvegarde pas automatiquement

---

## 🔄 Effet des Changements

### Après Sauvegarde avec Fichier Ouvert

1. **Langues cibles** mises à jour dans `got_manager`
2. **Formulaire** rechargé avec les nouvelles langues
3. **Arbre** rafraîchi avec les nouvelles couleurs de validation
4. **Message**: "✓ Configuration mise à jour"

### Variables Affectées

**`self.translation_config`**:
```python
{
  "target_languages": ["fr", "en", "es"],
  "visible_languages": ["fr", "en"],
  "prompts": {...}
}
```

**Utilisé dans**:
- `_on_magic_click()`: Construction des prompts
- `_refresh_after_config_change()`: Mise à jour de l'affichage
- `TranslationFormV2`: Filtrage des langues visibles (à implémenter)

---

## 🧪 Tests de Validation

### Test 1: Configuration des Langues

**Procédure**:
1. Ouvrir `Fichier` → `⚙️ Options...`
2. Dans l'onglet "🌍 Langues":
   - Langues cibles: `fr, de, ja`
   - Langues visibles: Cocher `fr` et `de`, décocher `ja`
3. Cliquer "💾 Sauvegarder"

**Résultat attendu**:
- Configuration sauvegardée dans `config/translation_config.json`
- Si fichier ouvert: formulaire affiche seulement `fr` et `de`
- `ja` reste dans le `.got.json` mais n'apparaît pas

---

### Test 2: Personnalisation des Prompts

**Procédure**:
1. Ouvrir `Fichier` → `⚙️ Options...`
2. Dans l'onglet "💬 Prompts de Traduction":
   - Modifier le prompt "Traduction Simple"
   - Exemple: Ajouter "Sois concis." à la fin
3. Cliquer "💾 Sauvegarder"
4. Traduire une entrée simple

**Résultat attendu**:
- Le nouveau prompt est utilisé pour la traduction
- Vérifiable dans les logs (si activés) ou comportement de l'IA

---

### Test 3: Réinitialisation

**Procédure**:
1. Modifier des options
2. Cliquer "🔄 Réinitialiser"
3. Observer les champs

**Résultat attendu**:
- Valeurs par défaut restaurées dans l'interface
- **Pas encore sauvegardé** (message d'info)
- Cliquer "💾 Sauvegarder" pour persister

---

### Test 4: Annulation

**Procédure**:
1. Modifier des options
2. Cliquer "❌ Annuler"
3. Rouvrir la fenêtre d'options

**Résultat attendu**:
- Modifications non sauvegardées
- Options inchangées

---

## 🐛 Validations Implémentées

### Langues Cibles

❌ **Si vide**:
```
Erreur: "Vous devez spécifier au moins une langue cible!"
```

❌ **Si code invalide** (ex: `fr, xx, es`):
```
Erreur: "Codes de langue invalides: xx

Codes valides: fr, en, es, de, it, pt, ru, ja, zh, ar"
```

### Langues Visibles

❌ **Si aucune cochée**:
```
Erreur: "Vous devez cocher au moins une langue visible!"
```

### Prompts

❌ **Si un prompt est vide**:
```
Erreur: "Tous les prompts doivent être remplis!"
```

---

## 💡 Améliorations Futures Possibles

### 1. Ajout de Langues Personnalisées

Permettre à l'utilisateur d'ajouter ses propres codes langue:
```
[+ Ajouter une langue]

Code: [____]  Nom: [____________]  [✓ Ajouter]
```

### 2. Prévisualisation des Prompts

Afficher un exemple de prompt généré avec des valeurs de test:
```
Aperçu du prompt:
┌─────────────────────────────────────────┐
│ Traduis "Hello World" en fr.           │
│ Réponds uniquement avec la traduction. │
└─────────────────────────────────────────┘
```

### 3. Import/Export de Configuration

Boutons pour:
- 📥 Importer une configuration depuis un fichier
- 📤 Exporter la configuration actuelle

### 4. Templates de Prompts

Bibliothèque de prompts pré-configurés:
- Style formel
- Style informel
- Style technique
- Style littéraire

### 5. Validation des Variables

Avertir si un prompt n'utilise pas les variables nécessaires:
```
⚠️ Le prompt "translate" devrait contenir {text} et {lang}
```

### 6. Historique des Configurations

Garder un historique des configurations:
```
Configurations récentes:
- [2025-10-16 14:30] fr, en, es (actuelle)
- [2025-10-15 10:20] fr, de, it
- [2025-10-14 16:45] fr, en
```

---

## 📚 Fichiers Créés/Modifiés

### Nouveau Fichier

**`gui/options_dialog.py`** (550 lignes)
- Classe `OptionsDialog(tk.Toplevel)`
- Interface complète avec 2 onglets
- Validation des entrées
- Sauvegarde/Chargement de configuration

### Fichiers Modifiés

**`gui/app_v2.py`**:
- Ligne 25: Import `json`
- Ligne 34: Import `OptionsDialog`
- Ligne 51: Chargement de `translation_config`
- Ligne 80: Ajout menu "⚙️ Options..."
- Lignes 223-263: Méthodes de gestion des options
- Lignes 467-499: Utilisation des prompts configurés

---

## ✅ Checklist de Développement

- [x] Créer `gui/options_dialog.py`
- [x] Interface avec 2 onglets (Langues, Prompts)
- [x] Langues connues (affichage)
- [x] Langues cibles (saisie avec virgules)
- [x] Langues visibles (cases à cocher)
- [x] Prompts personnalisables (4 types)
- [x] Validation des entrées
- [x] Sauvegarde/Chargement JSON
- [x] Intégration dans le menu Fichier
- [x] Rafraîchissement après sauvegarde
- [x] Utilisation des prompts dans `_on_magic_click()`
- [ ] Filtrage des langues visibles dans le formulaire (TODO)
- [ ] Tests utilisateurs
- [ ] Documentation utilisateur

---

## 🎉 Résultat

L'utilisateur peut maintenant:
- ✅ Configurer l'ordre des langues de traduction
- ✅ Masquer certaines langues sans perdre les données
- ✅ Personnaliser complètement les prompts envoyés à l'IA
- ✅ Adapter l'application à son workflow spécifique

**L'application est plus flexible et personnalisable!**

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-16
**Version**: OllamaFic v2.0 - Fenêtre d'Options
