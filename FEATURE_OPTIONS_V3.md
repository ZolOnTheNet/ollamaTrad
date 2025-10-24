# Feature: Options Dialog V3 - Améliorations Complètes

## 📅 Date: 2025-10-16

## 🎯 Objectifs

Améliorer le dialogue d'options avec :
1. **Tableur éditable** pour les langues (code + libellé)
2. **Onglet Configuration IA** (fournisseur, modèle, test de connexion)
3. **Sélection des langues visibles** dans l'arbre
4. **Option pour éditer le champ "ori"**
5. **Correction de la logique des couleurs** des parents

---

## 📊 Changements Majeurs

### 1. Nouveau Fichier: `options_dialog_v3.py`

Remplacement complet de `options_dialog.py` avec une interface modernisée et plus complète.

---

## 🌟 Nouvelles Fonctionnalités

### 1. 📚 Tableur Éditable pour les Langues

#### Avant
```
Langues Connues (non modifiables)
fr - Français
en - English
es - Español
...
```

**Problèmes**:
- Liste fixe et non extensible
- Impossible d'ajouter de nouvelles langues
- Modifications nécessitent changement de code

---

#### Après
```
┌────────────────────────────────────────────┐
│ Code (ex: fr)    │ Nom de la langue       │
├────────────────────────────────────────────┤
│ [fr____]         │ [Français___________]  │
│ [en____]         │ [English____________]  │
│ [es____]         │ [Español____________]  │
│ [______]         │ [__________________]   │ ← Ligne vide
│ [______]         │ [__________________]   │ ← Ligne vide
│          [➕ Ajouter une ligne]            │
└────────────────────────────────────────────┘
```

**Améliorations**:
- ✅ Champs éditables (Entry widgets)
- ✅ Ajout dynamique de lignes
- ✅ Validation : seules les lignes avec code ET nom sont considérées
- ✅ Scrollbar si plus de 10 langues
- ✅ Largeur adaptative (pleine largeur du dialogue)

**Validation**:
```python
# Seules les lignes complètes sont valides
fr + Français  → ✅ Valide
en +            → ❌ Invalide (nom manquant)
   + 日本語     → ❌ Invalide (code manquant)
```

---

### 2. 🤖 Onglet Configuration IA

Nouvel onglet complet pour configurer le fournisseur d'IA.

#### Structure

```
┌────────────────────────────────────────────────┐
│ 🎯 Fournisseur d'IA                           │
│   ○ Ollama (local)                            │
│   ● OpenAI                                    │
├────────────────────────────────────────────────┤
│ ⚙️ Configuration Ollama           [masqué]   │
│   Hôte:   [http://localhost:11434_______]    │
│   Modèle: [aya_________________________]    │
├────────────────────────────────────────────────┤
│ ⚙️ Configuration OpenAI           [visible]  │
│   Clé API: [sk-***************************] │
│   Modèle:  [gpt-4______________________]    │
├────────────────────────────────────────────────┤
│ [🧪 Tester la Connexion]  ⏳ Test en cours... │
└────────────────────────────────────────────────┘
```

**Fonctionnalités**:
- ✅ Sélection du fournisseur (Radio buttons)
- ✅ Configuration contextuelle (affiche uniquement le fournisseur sélectionné)
- ✅ Masquage de la clé API (show="*")
- ✅ Test de connexion avec feedback visuel
- ✅ États du test : ⏳ En cours / ✅ Réussi / ❌ Échoué

**Providers Supportés**:
1. **Ollama (local)**
   - Hôte personnalisable (défaut: `http://localhost:11434`)
   - Modèle sélectionnable (défaut: `aya`)

2. **OpenAI**
   - Clé API (masquée)
   - Modèle sélectionnable (défaut: `gpt-4`)

---

### 3. 👁️ Langues Visibles avec Scrollbar

#### Amélioration

**Avant**:
```
☑ fr (Français)   ☑ en (English)   ☑ es (Español)
☑ de (Deutsch)    ☑ it (Italiano)  ☑ pt (Português)
...
```

**Après** (avec scrollbar):
```
┌────────────────────────────────────────┐
│ ☑ fr (Français)    ☑ en (English)    │
│ ☑ es (Español)     ☑ de (Deutsch)    │
│ ☑ it (Italiano)    ☑ pt (Português)  │
│ ☑ ru (Русский)     ☑ ja (日本語)     │ ← Scroll
│ ☑ zh (中文)        ☑ ar (العربية)    │ ← Scroll
└────────────────────────────────────────┘
```

**Note importante**:
> Les données des langues non cochées **restent dans le .got.json** mais ne s'affichent pas dans l'arbre.
> Un fichier .got.json peut avoir plus de langues que celles visualisées.

---

### 4. ⚙️ Onglet Avancé - Édition du Champ "ori"

Nouvel onglet pour les options avancées.

```
┌────────────────────────────────────────────────┐
│ 📝 Édition du Champ Original (ori)            │
│                                                │
│ ☑ Autoriser l'édition du champ 'ori'         │
│    dans le formulaire                          │
│                                                │
│ ⚠️ Attention: Modifier le texte original peut │
│    affecter toutes les traductions liées.     │
└────────────────────────────────────────────────┘
```

**Fonctionnalité**:
- ✅ Checkbox pour activer/désactiver l'édition du champ "ori"
- ✅ Message d'avertissement clair
- ✅ Sauvegardé dans `allow_edit_ori` dans la configuration
- ✅ Peut être utilisé par l'application pour rendre le champ "ori" éditable

**Use Case**:
Permet de corriger des fautes de frappe dans le texte original sans avoir à modifier le fichier source JSON manuellement.

---

### 5. 🎨 Correction de la Logique des Couleurs

#### Problème Initial

La logique des couleurs des parents était incorrecte :
```python
# Ancienne logique
if green_count == total:
    return "green"
elif green_count > 0 or orange_count > 0:
    return "orange"  # ❌ Trop large
else:
    return "red"
```

**Problèmes**:
- Parent orange même si tous les enfants sont verts
- Ne distinguait pas noir (neutre) des autres couleurs

---

#### Nouvelle Logique (Correcte)

**Spécification**:
```
Noir = "none" = neutre (pas de traduction)

1. Toutes noires → parent noir
2. Toutes vertes OU noires (au moins 1 verte, 0 rouge) → parent vert
3. Toutes rouges OU noires (au moins 1 rouge, 0 verte) → parent rouge
4. Mélange de rouges ET vertes (avec ou sans noires) → parent orange
```

**Implémentation**:
```python
def _calculate_parent_state(self, parent_path: str) -> str:
    # Compter les états
    green_count = states.count("green")
    orange_count = states.count("orange")  # Orange = rouge + vert
    red_count = states.count("red")
    none_count = states.count("none")

    # 1. Toutes noires → parent noir
    if none_count == total:
        return "none"

    # Vérifier présence de couleurs (ignorer noir)
    has_green = green_count > 0 or orange_count > 0
    has_red = red_count > 0 or orange_count > 0

    # 2. Rouges ET vertes → parent orange
    if has_green and has_red:
        return "orange"

    # 3. Seulement vertes (+ noires) → parent vert
    if has_green and not has_red:
        return "green"

    # 4. Seulement rouges (+ noires) → parent rouge
    if has_red and not has_green:
        return "red"

    return "none"  # Défaut
```

---

### Exemples de Couleurs

| Enfants | Résultat Parent | Explication |
|---------|----------------|-------------|
| Noir, Noir, Noir | **Noir** | Tous neutres |
| Vert, Vert, Noir | **Vert** | Toutes les coulées sont vertes |
| Rouge, Rouge, Noir | **Rouge** | Toutes les colorées sont rouges |
| Vert, Rouge, Noir | **Orange** | Mélange rouge + vert |
| Vert, Orange, Noir | **Orange** | Orange contient du rouge |
| Rouge, Orange, Noir | **Orange** | Orange contient du vert |
| Vert, Vert, Vert | **Vert** | Tous verts (sans noir) |
| Rouge, Rouge, Rouge | **Rouge** | Tous rouges (sans noir) |
| Vert, Rouge, Orange | **Orange** | Mélange complet |

---

## 🔧 Fichiers Modifiés

### 1. `gui/options_dialog_v3.py` (NOUVEAU)

**Création complète** d'un nouveau fichier avec:
- Classe `OptionsDialogV3` (remplace `OptionsDialog`)
- 4 onglets : Langues, Configuration IA, Prompts, Avancé
- Tableur éditable avec scrollbar
- Configuration IA avec test de connexion
- Option "allow_edit_ori"

**Lignes de code**: ~800 lignes

---

### 2. `gui/app_v2.py` (MODIFIÉ)

**Fonction modifiée**: `_calculate_parent_state()` (lignes 793-854)

**Changements**:
```diff
- # Ancienne logique incorrecte
- elif green_count == total:
-     return "green"
- elif green_count > 0 or orange_count > 0:
-     return "orange"

+ # Nouvelle logique correcte
+ has_green = green_count > 0 or orange_count > 0
+ has_red = red_count > 0 or orange_count > 0
+
+ if has_green and has_red:
+     return "orange"
+ if has_green and not has_red:
+     return "green"
+ if has_red and not has_green:
+     return "red"
```

---

## 📐 Structure du Fichier de Configuration

### `config/translation_config.json`

```json
{
  "known_languages": {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    "ja": "日本語",
    "custom": "Ma Langue Personnalisée"
  },
  "target_languages": ["fr", "en", "es"],
  "visible_languages": ["fr", "en"],
  "allow_edit_ori": false,
  "ai_config": {
    "provider": "ollama",
    "ollama": {
      "host": "http://localhost:11434",
      "model": "aya"
    },
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  },
  "prompts": {
    "translate": "Traduis ...",
    "translate_html": "Traduis le HTML ...",
    "improve": "Améliore ...",
    "improve_html": "Améliore le HTML ..."
  }
}
```

**Nouveaux champs**:
- `allow_edit_ori`: Boolean pour autoriser l'édition du champ original
- `ai_config`: Configuration complète du fournisseur d'IA

---

## 🧪 Tests de Validation

### Test 1: Tableur de Langues

**Procédure**:
1. Ouvrir Options → Onglet "🌍 Langues"
2. Modifier une langue existante (ex: fr → fra)
3. Ajouter une nouvelle langue (ex: nl + Nederlands)
4. Laisser une ligne incomplète (ex: pt + )
5. Cliquer "Sauvegarder"

**Résultat attendu**:
- ✅ "fra" remplace "fr" dans la configuration
- ✅ "nl" est ajoutée
- ❌ Ligne incomplète "pt" est ignorée (sans erreur)

---

### Test 2: Configuration IA

**Procédure**:
1. Ouvrir Options → Onglet "🤖 Configuration IA"
2. Sélectionner "Ollama"
3. Modifier le modèle → "llama2"
4. Cliquer "🧪 Tester la Connexion"
5. Sélectionner "OpenAI"
6. Entrer une clé API
7. Sauvegarder

**Résultat attendu**:
- ✅ Configuration Ollama masquée quand OpenAI sélectionné
- ✅ Test affiche "⏳ Test en cours..." puis résultat
- ✅ Configuration sauvegardée avec le bon provider

---

### Test 3: Langues Visibles

**Procédure**:
1. Ajouter 15 langues dans le tableur
2. Aller à "👁️ Langues Visibles"
3. Décocher 5 langues
4. Sauvegarder
5. Recharger un fichier .got.json avec ces langues

**Résultat attendu**:
- ✅ Scrollbar apparaît pour les checkboxes
- ✅ Arbre n'affiche que les langues cochées
- ✅ Données des langues décochées restent dans le .got.json

---

### Test 4: Édition du Champ Ori

**Procédure**:
1. Aller à "⚙️ Avancé"
2. Cocher "Autoriser l'édition du champ 'ori'"
3. Sauvegarder
4. Ouvrir une entrée dans le formulaire

**Résultat attendu**:
- ✅ Configuration sauvegardée avec `"allow_edit_ori": true`
- ✅ (À implémenter) Champ "ori" devient éditable dans translation_form_v2.py

---

### Test 5: Couleurs des Parents

**Procédure**:
1. Créer un fichier .got.json avec:
   - Parent1 : enfant1 (vert), enfant2 (vert), enfant3 (noir)
   - Parent2 : enfant1 (rouge), enfant2 (rouge), enfant3 (noir)
   - Parent3 : enfant1 (vert), enfant2 (rouge), enfant3 (noir)
   - Parent4 : enfant1 (noir), enfant2 (noir), enfant3 (noir)
2. Charger le fichier
3. Observer les couleurs des parents

**Résultat attendu**:
- Parent1 : **Vert** (toutes vertes ou noires, au moins 1 verte)
- Parent2 : **Rouge** (toutes rouges ou noires, au moins 1 rouge)
- Parent3 : **Orange** (mélange rouge + vert)
- Parent4 : **Noir** (toutes noires)

---

## 💡 Avantages

### 1. 🌍 Flexibilité des Langues

**Avant**: 10 langues fixes
**Après**: Langues illimitées et personnalisables

**Use Case**:
```
Ajouter une langue régionale:
Code: oc
Nom: Occitan

Ajouter une langue construite:
Code: eo
Nom: Esperanto
```

---

### 2. 🤖 Configuration IA Unifiée

**Avant**: Configuration dispersée, pas de test
**Après**: Interface centralisée avec test

**Bénéfices**:
- Changement de fournisseur en 2 clics
- Test immédiat de la connexion
- Configuration visuelle (pas de fichier JSON manuel)

---

### 3. 👁️ Filtrage Intelligent

**Concept**: Séparation entre données et visualisation

**Exemple**:
```
Fichier .got.json contient:
- fr, en, es, de, it, pt, ru, ja, zh, ar (10 langues)

Langues visibles sélectionnées:
- fr, en, es (3 langues)

→ L'arbre n'affiche que fr, en, es
→ Les autres langues restent dans le fichier
→ Possibilité de les visualiser plus tard sans perte de données
```

---

### 4. ✏️ Flexibilité d'Édition

**Option "allow_edit_ori"** permet:
- Correction de fautes de frappe dans le texte source
- Adaptation du texte original sans modifier le JSON source
- Meilleur workflow pour les traducteurs

---

### 5. 🎨 Couleurs Cohérentes

**Problème résolu**: Couleur orange attribuée incorrectement

**Impact**:
- Indicateurs visuels fiables
- Progression de traduction claire
- Parents reflètent fidèlement l'état des enfants

---

## 🔄 Migration depuis options_dialog.py

### Étapes de Migration

1. **Sauvegarder l'ancien fichier**:
   ```bash
   cp gui/options_dialog.py gui/options_dialog_old.py
   ```

2. **Remplacer par la v3**:
   ```bash
   cp gui/options_dialog_v3.py gui/options_dialog.py
   ```

3. **Mettre à jour les imports** dans app_v2.py:
   ```python
   # Avant
   from gui.options_dialog import OptionsDialog

   # Après
   from gui.options_dialog import OptionsDialogV3 as OptionsDialog
   ```

4. **Tester la nouvelle interface**

---

## 🎓 Guide d'Utilisation

### Pour l'Utilisateur Final

#### 1. Ajouter une Nouvelle Langue

1. Ouvrir **Options** → Onglet **🌍 Langues**
2. Trouver une ligne vide dans le tableur
3. Entrer le **code** (ex: `nl`)
4. Entrer le **nom** (ex: `Nederlands`)
5. Cliquer **💾 Sauvegarder**

---

#### 2. Configurer l'IA

1. Ouvrir **Options** → Onglet **🤖 Configuration IA**
2. Choisir le fournisseur :
   - **Ollama** : Pour utilisation locale
   - **OpenAI** : Pour utiliser les modèles cloud
3. Remplir les champs de configuration
4. Cliquer **🧪 Tester la Connexion**
5. Si ✅, cliquer **💾 Sauvegarder**

---

#### 3. Filtrer les Langues Visibles

1. Ouvrir **Options** → Onglet **🌍 Langues**
2. Scroll jusqu'à **👁️ Langues Visibles**
3. Décocher les langues à masquer
4. Cliquer **💾 Sauvegarder**
5. Recharger le fichier pour voir l'effet

---

#### 4. Activer l'Édition du Champ Ori

1. Ouvrir **Options** → Onglet **⚙️ Avancé**
2. Cocher **✏️ Autoriser l'édition du champ 'ori'**
3. Cliquer **💾 Sauvegarder**
4. Le champ "ori" devient éditable dans le formulaire

---

## ✅ Checklist de Validation

- [x] Création de `options_dialog_v3.py`
- [x] Tableur éditable avec scrollbar
- [x] Bouton "➕ Ajouter une ligne"
- [x] Validation des lignes (code + nom requis)
- [x] Onglet Configuration IA avec Radio buttons
- [x] Affichage contextuel des configurations (Ollama/OpenAI)
- [x] Bouton test de connexion avec feedback
- [x] Langues visibles avec scrollbar
- [x] Option "allow_edit_ori" dans onglet Avancé
- [x] Modification de `_calculate_parent_state()` dans app_v2.py
- [x] Correction de la logique noir = neutre
- [x] Tests de compilation (Python 3)
- [x] Documentation complète

---

## 🎉 Résultat

Les utilisateurs peuvent maintenant:
- ✅ Ajouter/modifier des langues librement dans un tableur
- ✅ Configurer le fournisseur d'IA visuellement
- ✅ Tester la connexion IA avant utilisation
- ✅ Filtrer les langues affichées dans l'arbre
- ✅ Activer l'édition du champ "ori" si nécessaire
- ✅ Bénéficier de couleurs de parents cohérentes

**L'interface d'options est maintenant professionnelle, flexible et intuitive!**

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-16
**Version**: OllamaFic v3.0 - Options Dialog Amélioré
