# Fonctionnalité : Traduction Partielle (Sélection)

## Description

La fonctionnalité de traduction partielle permet de traduire ou améliorer uniquement une partie sélectionnée du texte dans les champs de traduction.

## Utilisation

1. **Sélectionner du texte** : Dans un champ de traduction (langue cible), sélectionnez une partie du texte que vous souhaitez traduire ou améliorer.

2. **Cliquer sur la baguette magique** : Cliquez sur le bouton 🪄 pour cette langue.

3. **Traduction automatique** :
   - Si le champ est vide ou que toute la sélection est vide : traduction complète de l'original
   - Si une partie du texte est sélectionnée : traduction/amélioration de la sélection uniquement

## Comportement

### Traduction de sélection
- Lorsque vous sélectionnez du texte dans un champ vide ou partiellement rempli
- Le système traduit uniquement la partie sélectionnée de l'original
- Le résultat remplace la sélection dans le champ

### Amélioration de sélection
- Lorsque vous sélectionnez du texte dans un champ déjà traduit
- Le système améliore uniquement la partie sélectionnée
- Le résultat remplace la sélection dans le champ
- L'ancien texte complet est sauvegardé dans l'historique

## Historique

L'historique de traduction est automatiquement mis à jour :
- Avant chaque traduction partielle, le texte complet est sauvegardé dans l'historique
- Vous pouvez utiliser les boutons ↶ (undo) et ↷ (redo) pour naviguer dans l'historique
- L'historique vous permet de revenir à n'importe quelle version précédente

## Cas d'usage

### Correction d'une partie problématique
```
Texte original : "The quick brown fox jumps over the lazy dog."
Traduction initiale : "Le rapide renard brun saute par-dessus le chien paresseux."

Problème : "Le rapide renard" n'est pas idiomatique en français

Solution :
1. Sélectionner "Le rapide renard"
2. Cliquer sur 🪄
3. Le système propose "Le renard rapide" ou "Le renard véloce"
4. Le résultat : "Le renard rapide brun saute par-dessus le chien paresseux."
```

### Traduction progressive
```
Texte long avec plusieurs parties :
1. Traduire d'abord la partie principale
2. Sélectionner et traduire les parties spécifiques une par une
3. Affiner chaque partie individuellement
```

## Avantages

1. **Précision** : Permet de corriger uniquement les parties problématiques sans refaire toute la traduction
2. **Efficacité** : Évite de renvoyer tout le texte à l'IA, surtout pour de longs textes
3. **Contrôle** : Donne plus de contrôle sur la traduction finale
4. **Historique** : Toutes les modifications sont tracées et réversibles

## Notes techniques

- Les index de sélection sont conservés pour un remplacement précis
- Le texte avant et après la sélection est préservé
- L'historique complet est maintenu pour chaque modification
- Les prompts IA sont adaptés selon qu'il s'agit d'une sélection ou du texte complet
