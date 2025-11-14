# Plan de Test - OllamaTrad v2.0 GUI

## 📅 Date: 2025-10-16

Ce document fournit un plan de test complet pour valider toutes les corrections apportées.

---

## 🎯 Objectif

Vérifier que tous les bugs signalés ont été corrigés et que l'application fonctionne correctement.

---

## ✅ Tests de Base

### Test 1: Chargement Initial

**Procédure**:
1. Lancer l'application: `python ollamaTrad.py --gui`
2. Ouvrir un fichier .got.json existant
3. Observer l'arbre de navigation

**Résultats attendus**:
- ✅ L'arbre se charge sans erreur
- ✅ Les entrées **sans traductions** sont **noires** (pas rouges!)
- ✅ Les entrées avec traductions non validées sont rouges
- ✅ Les entrées avec traductions validées sont vertes
- ✅ Les entrées partiellement traduites sont orange

**Vérification**:
```
□ Arbre chargé correctement
□ Couleurs correctes (noir pour entrées vides)
□ Pas d'erreurs dans la console
```

---

### Test 2: Affichage du Chemin Actuel

**Procédure**:
1. Sélectionner différentes entrées dans l'arbre
2. Observer le label "Chemin actuel:" au-dessus de l'arbre

**Résultats attendus**:
- ✅ Le chemin s'affiche en bleu
- ✅ Le chemin change à chaque sélection
- ✅ Format: `entries/Entry Name/field_name`

**Vérification**:
```
□ Chemin affiché et visible
□ Se met à jour à chaque clic
□ Affiche le bon path
```

---

### Test 3: Largeur des Champs

**Procédure**:
1. Sélectionner une entrée avec du texte long
2. Observer la largeur du champ "Original (ori)"
3. Observer la largeur des champs de traduction

**Résultats attendus**:
- ✅ Les champs utilisent **toute la largeur disponible**
- ✅ Pas d'espace vide à droite
- ✅ Texte visible sans scroll horizontal

**Vérification**:
```
□ Champs prennent toute la largeur
□ Pas d'espace vide inutile
□ Lisibilité optimale
```

---

## 🔧 Tests de Traduction

### Test 4: Traduction Simple (Entry Switching Fix)

**⚠️ TEST CRITIQUE - Vérification du bug principal**

**Procédure**:
1. Sélectionner une entrée avec `name` et `description` vides
2. Cliquer 🪄 sur `name[fr]`
3. **Attendre** la fin de la traduction
4. Noter le résultat de `name[fr]`
5. Cliquer 🪄 sur `description[fr]`
6. **Vérifier** que `description[fr]` reçoit SA traduction

**Résultats attendus**:
- ✅ `name[fr]` traduit correctement (ex: "Gardien de la cachette")
- ✅ `description[fr]` traduit correctement le HTML (ex: "<h1>Détails</h1>...")
- ✅ `description[fr]` **NE contient PAS** la traduction de `name`
- ✅ Pas de réutilisation de la traduction précédente

**Exemple concret**:
```
name (original): "Vault Guardian Gaoler"
name[fr] (attendu): "Gardien de la cachette" ✅

description (original): "<h1>Details</h1><p>A boxy construct</p>"
description[fr] (attendu): "<h1>Détails</h1><p>Un construct carré</p>" ✅
description[fr] (INCORRECT): "Gardien du coffre" ❌ ← Si ceci apparaît, le bug existe encore!
```

**Vérification**:
```
□ name traduit correctement
□ description traduit correctement (pas la traduction de name!)
□ Pas de pollution entre les traductions
□ clear_conversation() fonctionne
```

---

### Test 5: Traductions Séquentielles Multiples

**Procédure**:
1. Charger un fichier avec plusieurs entrées
2. Traduire Entry1/name → noter le résultat
3. Traduire Entry2/name → noter le résultat
4. Traduire Entry3/description → noter le résultat
5. Vérifier que chaque traduction est unique et correcte

**Résultats attendus**:
- ✅ Chaque entrée reçoit SA propre traduction
- ✅ Pas de répétitions ni variations d'une traduction précédente
- ✅ Traductions cohérentes avec le texte original

**Vérification**:
```
□ Entry1 traduit correctement
□ Entry2 traduit correctement (différent de Entry1)
□ Entry3 traduit correctement (différent de Entry1 et Entry2)
□ Aucune pollution contextuelle
```

---

### Test 6: Préservation du HTML

**Procédure**:
1. Sélectionner une entrée avec du HTML (ex: description)
2. Vérifier le contenu original contient des balises HTML
3. Cliquer 🪄 pour traduire
4. Vérifier le résultat

**Exemples de HTML**:
```html
<!-- Cas simple -->
<h1>Details</h1><p>Description text</p>

<!-- Cas complexe -->
<h1>Title</h1>
<h4>SUBTITLE</h4>
<p>Paragraph with <strong>bold</strong> text</p>
<ul><li>Item 1</li><li>Item 2</li></ul>
```

**Résultats attendus**:
- ✅ Toutes les balises HTML sont **préservées**
- ✅ Seul le texte **entre les balises** est traduit
- ✅ Structure HTML identique avant/après traduction

**Vérification**:
```
□ Balises <h1>, <p>, <ul>, <li>, <strong> préservées
□ Texte traduit correctement
□ Structure HTML intacte
```

---

### Test 7: Timeout Textes Longs

**Procédure**:
1. Sélectionner une description longue (> 500 mots)
2. Cliquer 🪄 pour traduire
3. Attendre jusqu'à 2 minutes si nécessaire

**Résultats attendus**:
- ✅ Pas d'erreur de timeout avant 120 secondes
- ✅ Traduction complète reçue
- ✅ Application reste responsive pendant la traduction

**Vérification**:
```
□ Pas d'erreur de timeout
□ Traduction complète obtenue
□ Application ne freeze pas
```

---

## 🎨 Tests d'Interface

### Test 8: Historique Chat

**Procédure**:
1. Sélectionner une entrée
2. Cliquer 🪄 pour traduire
3. Observer le panneau historique (en bas)

**Résultats attendus**:
- ✅ Message système **AVANT** traduction: `"FR: Traduire → 'texte original'"`
- ✅ Message résultat **APRÈS** traduction: `"🪄 FR: traduire 'résultat' [✓/❌ validation]"`
- ✅ Texte original visible dans l'historique

**Vérification**:
```
□ Message "Traduire → " affiché avant
□ Texte original visible
□ Résultat affiché après
□ État de validation visible
```

---

### Test 9: Toggle Chat

**Procédure**:
1. Observer la taille du panneau chat (en bas)
2. Cliquer sur le bouton "▼" pour masquer
3. Observer le redimensionnement
4. Cliquer sur "▶" pour afficher à nouveau

**Résultats attendus**:
- ✅ Clic sur ▼: Chat se cache ET pane se redimensionne
- ✅ Formulaire gagne de l'espace vertical
- ✅ Clic sur ▶: Chat réapparaît ET pane se redimensionne
- ✅ Formulaire perd de l'espace vertical

**Vérification**:
```
□ Chat se cache/affiche correctement
□ Pane se redimensionne automatiquement
□ Pas d'espace vide perdu
□ Sash se déplace correctement
```

---

### Test 10: Multi-lignes et Auto-resize

**Procédure**:
1. Sélectionner une entrée avec texte court (ex: name)
2. Observer la hauteur du champ → doit être ~3 lignes
3. Sélectionner une entrée avec texte long (ex: description)
4. Observer la hauteur du champ → doit être plus grand

**Résultats attendus**:
- ✅ Texte court: champ petit (3 lignes)
- ✅ Texte long: champ grand (jusqu'à 10 lignes)
- ✅ Ascenseur vertical si > 10 lignes
- ✅ Champs modifiables (pas en lecture seule)

**Vérification**:
```
□ Hauteur s'adapte au contenu
□ Min 3 lignes, max 10 lignes
□ Ascenseur si nécessaire
□ Édition possible
```

---

## 🔄 Tests de Workflow

### Test 11: Édition Manuelle

**Procédure**:
1. Sélectionner une entrée traduite
2. Modifier manuellement le texte dans le champ `fr`
3. **Cliquer ailleurs** (FocusOut)
4. Observer l'historique et les couleurs

**Résultats attendus**:
- ✅ Changement détecté **seulement à la sortie du champ** (pas pendant frappe)
- ✅ Historique mis à jour
- ✅ Couleur mise à jour
- ✅ Fichier marqué comme modifié

**Vérification**:
```
□ Pas de détection pendant frappe
□ Détection à FocusOut
□ Historique mis à jour
□ Couleur actualisée
```

---

### Test 12: Validation/Invalidation

**Procédure**:
1. Traduire une entrée (devient rouge)
2. Cocher la case ✓ pour valider (devient vert)
3. Décocher la case (redevient rouge)
4. Observer les couleurs parent

**Résultats attendus**:
- ✅ Rouge: traduction non validée
- ✅ Vert: traduction validée
- ✅ Orange: si plusieurs langues, certaines validées
- ✅ Parent prend la couleur la "moins bonne" de ses enfants

**Vérification**:
```
□ Couleurs changent correctement
□ Parents reflètent l'état des enfants
□ Validation enregistrée dans .got.json
```

---

### Test 13: Rollback (Historique)

**Procédure**:
1. Traduire une entrée (historique vide)
2. Améliorer la traduction (historique contient 1 item)
3. Cliquer sur le bouton ↶ (rollback)
4. Observer le résultat

**Résultats attendus**:
- ✅ Texte revient à la version précédente
- ✅ Historique diminue de 1 item
- ✅ Bouton ↶ se désactive si historique vide

**Vérification**:
```
□ Rollback fonctionne
□ Historique géré correctement
□ Bouton désactivé si vide
```

---

### Test 14: Action "Améliorer"

**Procédure**:
1. Traduire une entrée (champ vide → texte)
2. Cliquer 🪄 à nouveau (amélioration)
3. Observer le prompt dans l'historique

**Résultats attendus**:
- ✅ Premier clic: action = "translate"
- ✅ Deuxième clic: action = "improve"
- ✅ Prompt inclut texte original ET traduction actuelle
- ✅ Résultat est une amélioration de la traduction existante

**Vérification**:
```
□ Action détectée correctement
□ Prompt approprié envoyé
□ Amélioration cohérente avec original
```

---

## 🌍 Tests Multi-langues

### Test 15: Traductions Multiples Langues

**Procédure**:
1. Configurer plusieurs langues cibles (fr, es, de)
2. Sélectionner une entrée
3. Traduire en `fr`
4. Traduire en `es`
5. Traduire en `de`

**Résultats attendus**:
- ✅ Chaque langue reçoit SA traduction
- ✅ Pas de pollution entre langues
- ✅ Traductions cohérentes avec la langue cible

**Exemple**:
```
original: "Guardian"
fr: "Gardien" ✅
es: "Guardián" ✅ (pas "Gardien"!)
de: "Wächter" ✅ (pas "Guardián"!)
```

**Vérification**:
```
□ fr traduit en français
□ es traduit en espagnol (pas français!)
□ de traduit en allemand (pas espagnol/français!)
□ Aucune pollution entre langues
```

---

## 🐛 Tests de Régression

### Test 16: Changement d'Entrée Pendant Traduction

**Procédure**:
1. Sélectionner Entry A
2. Cliquer 🪄 sur `fr`
3. **Immédiatement** sélectionner Entry B (pendant traduction)
4. Attendre fin de traduction
5. Vérifier où la traduction a été écrite

**Résultats attendus**:
- ✅ Traduction écrite dans **Entry A** (pas Entry B)
- ✅ Formulaire affiche **Entry B** (pas Entry A)
- ✅ Message: "Traduction terminée pour Entry A"
- ✅ Pas d'erreur, pas de confusion

**Vérification**:
```
□ Traduction écrite au bon endroit (Entry A)
□ Formulaire affiche Entry B
□ Message explicite
□ Variables capturées fonctionnent
```

---

### Test 17: Clics Rapides Multiples

**Procédure**:
1. Sélectionner une entrée
2. Cliquer 🪄 sur `fr`
3. **Immédiatement** cliquer 🪄 sur `es`
4. **Immédiatement** cliquer 🪄 sur `de`
5. Attendre que toutes les traductions se terminent

**Résultats attendus**:
- ✅ 3 threads lancés en parallèle
- ✅ Chaque thread indépendant
- ✅ Pas de race conditions
- ✅ Chaque langue reçoit sa traduction

**Vérification**:
```
□ Toutes les traductions se terminent
□ Aucune erreur
□ Résultats corrects
□ Pas de confusion entre threads
```

---

## 📊 Résultats Attendus

### Checklist Globale

```
✅ Test 1:  Chargement Initial
✅ Test 2:  Affichage Chemin Actuel
✅ Test 3:  Largeur des Champs
✅ Test 4:  Traduction Simple (CRITIQUE)
✅ Test 5:  Traductions Séquentielles
✅ Test 6:  Préservation HTML
✅ Test 7:  Timeout Textes Longs
✅ Test 8:  Historique Chat
✅ Test 9:  Toggle Chat
✅ Test 10: Multi-lignes Auto-resize
✅ Test 11: Édition Manuelle
✅ Test 12: Validation/Invalidation
✅ Test 13: Rollback
✅ Test 14: Action Améliorer
✅ Test 15: Traductions Multi-langues
✅ Test 16: Changement Pendant Traduction
✅ Test 17: Clics Rapides Multiples
```

---

## 🚨 Problèmes à Signaler

Si l'un des tests échoue, noter:

1. **Numéro du test**: Test X échoué
2. **Comportement observé**: Ce qui s'est passé
3. **Comportement attendu**: Ce qui devrait se passer
4. **Console logs**: Messages d'erreur dans la console
5. **Étapes de reproduction**: Comment reproduire le bug

**Format de rapport**:
```
Test X échoué: [Nom du test]

Observé:
- [Description du comportement observé]

Attendu:
- [Description du comportement attendu]

Logs:
```
[Copier les logs console]
```

Reproduction:
1. [Étape 1]
2. [Étape 2]
...
```

---

## ✅ Conclusion

Si **tous les tests passent**, l'application est prête pour utilisation en production.

**Tests critiques à absolument valider**:
- ✅ Test 4: Traduction Simple (Entry Switching) → Correction principale
- ✅ Test 6: Préservation HTML → Feature importante
- ✅ Test 15: Multi-langues → Pas de pollution

**Priorités de test**:
1. **Haute**: Tests 4, 6, 15 (fonctionnalités critiques)
2. **Moyenne**: Tests 1, 2, 5, 7, 8 (interface et fiabilité)
3. **Basse**: Tests 9-14, 16-17 (edge cases et UX)

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-16
**Version**: OllamaTrad v2.0 - Plan de Test
