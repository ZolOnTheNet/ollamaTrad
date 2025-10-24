# Fonctionnalité : Sélection de la Langue d'Origine

## Description

La fonctionnalité de sélection de langue d'origine permet de spécifier la langue du texte source pour améliorer la qualité des traductions. Cela aide l'IA à mieux comprendre le contexte et à produire des traductions plus précises.

## Interface

Un combobox "Langue d'origine" est situé dans le formulaire de traduction, juste après le chemin de l'entrée et avant le texte original.

### Langues disponibles

- **auto** (par défaut) : Détection automatique de la langue
- **en** : Anglais
- **fr** : Français
- **es** : Espagnol
- **de** : Allemand
- **it** : Italien
- **pt** : Portugais
- **ru** : Russe
- **ja** : Japonais
- **zh** : Chinois
- **ko** : Coréen
- **ar** : Arabe

## Utilisation

### Sélection de la langue

1. Ouvrez une entrée traduisible dans le formulaire
2. Cliquez sur le combobox "Langue d'origine"
3. Sélectionnez la langue du texte original
4. La langue sélectionnée sera utilisée pour toutes les traductions de cette entrée

### Mode automatique

- Par défaut, la langue est réglée sur "auto"
- L'IA détecte automatiquement la langue du texte source
- Convient pour la plupart des cas d'usage

### Spécification manuelle

- Utilisez une langue spécifique quand :
  - Le texte contient du vocabulaire technique
  - La détection automatique peut être ambiguë
  - Vous voulez forcer une interprétation particulière
  - Le texte mélange plusieurs langues (choisissez la principale)

## Impact sur les prompts

### Mode automatique (auto)

```
Prompt : Traduis "Hello World" en fr. Réponds uniquement avec la traduction, sans explication.
```

### Mode manuel (ex: anglais → français)

```
Prompt : Traduis "Hello World" depuis l'anglais en fr. Réponds uniquement avec la traduction, sans explication.
```

### Avec HTML

```
Prompt : Traduis le texte suivant depuis l'anglais en fr.
IMPORTANT: Préserve TOUTES les balises HTML.

<p>Hello <strong>World</strong></p>
```

### Pour l'amélioration

```
Prompt : Améliore cette traduction depuis l'anglais vers fr:
Original: "Hello World"
Actuel: "Bonjour le monde"
Contexte: app/greeting/message
```

## Avantages

### 1. Précision améliorée

- L'IA comprend mieux le contexte source
- Réduit les ambiguïtés de traduction
- Améliore la cohérence terminologique

### 2. Traductions techniques

- Meilleure gestion des termes spécialisés
- Préservation des nuances techniques
- Adaptation culturelle appropriée

### 3. Textes multilingues

- Permet de spécifier la langue principale
- Aide l'IA à identifier les éléments à traduire
- Évite la confusion entre langues similaires

## Exemples d'utilisation

### Cas 1 : Texte technique anglais

```
Texte original (en) : "The API endpoint returns a JSON response"
Langue d'origine : en
Langue cible : fr

Avec "auto" : "Le point de terminaison API renvoie une réponse JSON"
Avec "en" : "Le point de terminaison de l'API renvoie une réponse JSON"
```

### Cas 2 : Texte avec faux-amis

```
Texte original (es) : "El conductor estaba cansado"
Langue d'origine : es
Langue cible : fr

Avec "auto" : "Le conducteur était fatigué" (peut confondre avec anglais)
Avec "es" : "Le conducteur était fatigué" (comprend que c'est espagnol)
```

### Cas 3 : Texte court ambigu

```
Texte original : "Chat"
Langue d'origine : en vs fr

Avec "en" → fr : "Discussion" ou "Bavardage"
Avec "fr" → en : "Cat"
```

## Cas d'usage recommandés

### Utilisez "auto" pour :

- Textes longs et clairs
- Langues très distinctes
- Traductions générales
- Gain de temps

### Spécifiez la langue pour :

- Textes courts (< 20 mots)
- Vocabulaire technique ou spécialisé
- Langues proches (es/pt, fr/it)
- Textes contenant des acronymes
- Noms propres ambigus
- Maximum de précision requis

## Notes techniques

### Implémentation

- La langue sélectionnée est passée à chaque appel de traduction
- Elle est utilisée pour construire des prompts plus précis
- Elle affecte tous les types d'opérations (translate, improve, selection)
- Le réglage persiste tant que l'entrée est ouverte

### Mapping des langues

Les codes de langue sont convertis en noms complets pour les prompts :

```python
lang_names = {
    "en": "anglais",
    "fr": "français",
    "es": "espagnol",
    "de": "allemand",
    "it": "italien",
    "pt": "portugais",
    "ru": "russe",
    "ja": "japonais",
    "zh": "chinois",
    "ko": "coréen",
    "ar": "arabe"
}
```

### Prompts modifiés

Tous les prompts sont adaptés pour inclure la langue source quand elle est spécifiée :

1. **translate** : `Traduis "{text}"{source_lang} en {lang}`
2. **translate_html** : `Traduis le texte suivant{source_lang} en {lang}`
3. **improve** : `Améliore cette traduction{source_lang} vers {lang}`
4. **improve_html** : `Améliore cette traduction{source_lang} vers {lang}`
5. **improve_selection** : `Améliore cette partie de traduction{source_lang} vers {lang}`
6. **improve_selection_html** : `Améliore cette partie de traduction{source_lang} vers {lang}`

Où `{source_lang}` est :
- Vide si "auto"
- " depuis le [langue]" si spécifié (ex: " depuis l'anglais")
