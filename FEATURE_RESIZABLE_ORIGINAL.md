# Fonctionnalité : Zone Original Redimensionnable

## Description

La zone de texte original peut maintenant être redimensionnée verticalement en déplaçant la barre de séparation entre "Original (ori)" et "Traductions".

## Utilisation

### Redimensionner la zone original

1. **Localiser la barre de séparation** : Entre la zone "Original (ori)" et la zone "Traductions"
2. **Survoler la barre** : Le curseur change pour indiquer que c'est redimensionnable
3. **Cliquer et glisser** :
   - Glisser vers le **bas** → Agrandit la zone original
   - Glisser vers le **haut** → Réduit la zone original

### Interface

```
┌─────────────────────────────────────────────────┐
│ 📍 Chemin: app/description                     │
│ ─────────────────────────────────────────────── │
│ Langue d'origine: [auto ▼]                     │
│ ─────────────────────────────────────────────── │
│                                                 │
│ Original (ori):                                 │
│ ┌─────────────────────────────────────────────┐│
│ │ This is a very long text that needs more   ││
│ │ space to be properly displayed. You can    ││
│ │ now resize this area by dragging the       ││
│ │ separator bar below.                        ││
│ └─────────────────────────────────────────────┘│
│                                                 │
├═════════════════════════════════════════════════┤ ← Barre redimensionnable
│                                                 │
│ Traductions:                                    │
│ ┌─────────────────────────────────────────────┐│
│ │ 🪄 FR: [texte français...]                  ││
│ │ 🪄 EN: [texte anglais...]                   ││
│ └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

## Cas d'usage

### 1. Texte original court

Pour un titre court comme "Hello World" :
- **Réduire la zone original** pour gagner de l'espace
- Plus d'espace pour les traductions multiples

### 2. Texte original long

Pour une description de plusieurs paragraphes :
- **Agrandir la zone original** pour lire confortablement
- Voir tout le contexte sans défilement constant

### 3. Texte HTML complexe

Pour du HTML avec beaucoup de balises :
```html
<div class="container">
  <h1>Welcome to our <strong>amazing</strong> application</h1>
  <p>This is a long description that explains all the features...</p>
</div>
```
- **Agrandir significativement** pour voir la structure HTML
- Facilite la vérification que toutes les balises sont préservées

## Comportement

### Poids des zones

- **Zone original** : `weight=0`
  - Taille initiale fixe (height=5)
  - Ne s'agrandit pas automatiquement quand on redimensionne la fenêtre

- **Zone traductions** : `weight=1`
  - S'adapte automatiquement à l'espace restant
  - S'agrandit quand on redimensionne la fenêtre

### Limites

- **Minimum** : On ne peut pas réduire complètement une zone (minimum ~30 pixels)
- **Maximum** : La zone original peut prendre presque toute la hauteur si nécessaire

### Persistance

⚠️ **Attention** : Le redimensionnement n'est pas persistant entre les sessions.
- Chaque nouvelle entrée ouverte réinitialise la taille par défaut
- À implémenter : Sauvegarder la position du séparateur dans les préférences utilisateur

## Détails techniques

### Implémentation

#### translation_form_v2.py (lignes 115-152)

```python
# PanedWindow vertical pour séparer original et traductions
self.paned_window = ttk.PanedWindow(self, orient="vertical")
self.paned_window.pack(fill="both", expand=True, padx=10, pady=(0, 5))

# === HAUT: Zone original (ori) ===
ori_container = ttk.Frame(self.paned_window)
self.paned_window.add(ori_container, weight=0)  # Ne s'agrandit pas auto

# === BAS: Section traductions ===
translations_container = ttk.Frame(self.paned_window)
self.paned_window.add(translations_container, weight=1)  # S'adapte
```

### Structure

Avant (fixe) :
```
Frame (self)
├─ top_frame (pack fill="x")
│  ├─ header
│  ├─ source_lang
│  └─ ori_frame (fixe, height=3)
└─ translations_frame (pack fill="both", expand=True)
```

Après (redimensionnable) :
```
Frame (self)
├─ header_frame (pack fill="x")
│  ├─ header
│  └─ source_lang
└─ paned_window (pack fill="both", expand=True)
   ├─ ori_container (weight=0)
   │  └─ ori_text (height=5, redimensionnable)
   └─ translations_container (weight=1)
      └─ translations_frame (scrollable)
```

### Changements clés

1. **Séparation des sections** : Header séparé du PanedWindow
2. **PanedWindow** : Permet le redimensionnement interactif
3. **Weight** : Contrôle comment les zones se comportent lors du redimensionnement de la fenêtre
4. **Height initial** : Passé de 3 à 5 lignes pour mieux utiliser l'espace

## Avantages

✅ **Flexibilité** : Adapter l'interface selon le contenu

✅ **Confort** : Lire les longs textes sans défilement constant

✅ **Efficacité** : Gagner de l'espace pour les textes courts

✅ **Intuitivité** : Interaction standard (glisser-déposer)

✅ **Accessibilité** : Mieux voir le contexte lors de la traduction

## Améliorations futures

### 1. Persistance de la position

Sauvegarder la position du séparateur :
```python
# Dans un fichier de configuration
{
  "ui_preferences": {
    "original_pane_height": 150
  }
}
```

### 2. Boutons rapides

Ajouter des boutons pour les tailles prédéfinies :
```
[Petit] [Moyen] [Grand]
```

### 3. Double-clic pour auto-ajuster

Double-cliquer sur la barre pour ajuster automatiquement à la hauteur du contenu.

### 4. Position par type de contenu

Mémoriser différentes positions selon le type :
- Textes courts (titres) : petit
- Textes moyens (descriptions) : moyen
- HTML/Markdown : grand

## Comparaison

### Avant

**Inconvénients** :
- Hauteur fixe de 3 lignes
- Beaucoup de défilement pour les longs textes
- Gaspillage d'espace pour les textes courts

### Après

**Avantages** :
- Hauteur ajustable à volonté
- Confort de lecture pour tous les types de textes
- Utilisation optimale de l'espace disponible
- Interaction intuitive

Cette amélioration rend l'interface beaucoup plus flexible et agréable à utiliser !
