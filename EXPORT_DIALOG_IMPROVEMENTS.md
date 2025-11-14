# Améliorations du dialogue d'export

## Modifications apportées

### 1. Sélecteur de fichier classique

**Avant** : Sélection manuelle avec deux champs séparés (répertoire + nom de fichier)

**Après** : Utilisation du sélecteur de fichier natif `filedialog.asksaveasfilename()`

#### Avantages

✅ **Interface familière** : Dialogue standard de sauvegarde de fichier que tous les utilisateurs connaissent

✅ **Filtres de types** : Affichage des fichiers JSON/GOT.JSON existants dans le répertoire

✅ **Navigation facilitée** : Possibilité de naviguer librement dans l'arborescence

✅ **Autocomplétion** : Suggestions de noms de fichiers existants

✅ **Détection automatique** : Avertissement si le fichier existe déjà (géré par le système + notre code)

### 2. Structure du dialogue améliorée

```
┌─────────────────────────────────────────────────────────┐
│ 📤 Export vers JSON                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ╔═════════════════════════════════════════════════════╗ │
│ ║ Langue cible                                        ║ │
│ ╚═════════════════════════════════════════════════════╝ │
│   Langue: [FR ▼]                                        │
│                                                         │
│ ╔═════════════════════════════════════════════════════╗ │
│ ║ Fichier de destination                              ║ │
│ ╚═════════════════════════════════════════════════════╝ │
│   Fichier: [/path/to/app-fr.json] [Parcourir...]      │
│                                                         │
│ ╔═════════════════════════════════════════════════════╗ │
│ ║ Mode d'export                                       ║ │
│ ╚═════════════════════════════════════════════════════╝ │
│   ○ Standard                                            │
│      ℹ️ Export identique au JSON original, avec        │
│         traduction prioritaire si définie               │
│                                                         │
│   ● Unique Validé                                      │
│      ℹ️ N'exporte que les traductions validées et      │
│         non vides, sinon l'original                     │
│                                                         │
│                          [Annuler] [Exporter]           │
└─────────────────────────────────────────────────────────┘
```

### 3. Workflow utilisateur

#### Avant

1. Cliquer sur "Parcourir..." pour choisir le répertoire
2. Taper manuellement le nom du fichier
3. Vérifier que tout est correct
4. Cliquer sur "Exporter"

#### Après

1. Cliquer sur "Parcourir..."
2. **→ Dialogue natif s'ouvre avec :**
   - Répertoire actuel pré-sélectionné
   - Nom de fichier pré-rempli (`app-fr.json`)
   - Filtres pour voir les fichiers JSON existants
   - Navigation complète dans l'arborescence
3. Choisir ou modifier le fichier
4. Cliquer sur "Enregistrer" dans le dialogue natif
5. **→ Retour au dialogue principal**
6. Cliquer sur "Exporter"

## Détails techniques

### Sélecteur de fichier natif

```python
def _browse_file(self):
    """Ouvre un dialogue de sélection de fichier classique."""
    filepath = filedialog.asksaveasfilename(
        parent=self.dialog,
        title="Enregistrer le fichier JSON",
        initialdir=str(Path(current_path).parent),
        initialfile=Path(current_path).name,
        defaultextension=".json",
        filetypes=[
            ("Fichiers JSON", "*.json"),
            ("Fichiers GOT.JSON", "*.got.json"),
            ("Tous les fichiers", "*.*")
        ]
    )

    if filepath:
        self.output_path_var.set(filepath)
```

### Paramètres

| Paramètre | Description | Valeur |
|-----------|-------------|--------|
| `parent` | Fenêtre parente | `self.dialog` |
| `title` | Titre du dialogue | "Enregistrer le fichier JSON" |
| `initialdir` | Répertoire initial | Même que le fichier .got.json |
| `initialfile` | Nom pré-rempli | `app-fr.json` (généré automatiquement) |
| `defaultextension` | Extension par défaut | `.json` |
| `filetypes` | Filtres de types | JSON, GOT.JSON, Tous |

### Filtres de types de fichiers

Le dialogue affiche une combobox avec 3 options :

```
[Fichiers JSON (*.json) ▼]
  ├─ Fichiers JSON (*.json)
  ├─ Fichiers GOT.JSON (*.got.json)
  └─ Tous les fichiers (*.*)
```

**Bénéfice** : L'utilisateur peut voir les fichiers JSON existants dans le répertoire et choisir d'écraser un fichier existant ou créer un nouveau nom.

### Validation

La validation reste la même mais utilise maintenant `output_path_var` :

```python
def _on_export(self):
    """Valide et ferme le dialogue."""
    # Validation de la langue
    lang = self.lang_var.get()
    if not lang:
        messagebox.showerror("Erreur", "Veuillez sélectionner une langue")
        return

    # Validation du fichier
    output_path_str = self.output_path_var.get()
    if not output_path_str:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier")
        return

    output_path = Path(output_path_str)

    # Vérifier que le répertoire parent existe
    if not output_path.parent.exists():
        messagebox.showerror("Erreur", f"Répertoire inexistant")
        return

    # Ajouter .json si manquant
    if not output_path.suffix:
        output_path = output_path.with_suffix('.json')

    # Vérifier si le fichier existe déjà (double vérification)
    if output_path.exists():
        response = messagebox.askyesno(
            "Fichier existant",
            f"Voulez-vous remplacer '{output_path.name}' ?"
        )
        if not response:
            return

    # Succès
    self.result = {
        'language': lang,
        'output_path': str(output_path),
        'mode': self.export_mode_var.get()
    }
    self.dialog.destroy()
```

## Exemple d'utilisation

### Scénario : Exporter en français

1. **Menu** : Fichier → Exporter vers JSON... → FR

2. **Dialogue principal s'ouvre** :
   ```
   Langue: FR
   Fichier: /home/user/documents/app-fr.json
   Mode: ○ Standard
   ```

3. **Cliquer sur "Parcourir..."**

4. **Dialogue natif s'ouvre** :
   ```
   ┌─────────────────────────────────────────────────┐
   │ Enregistrer le fichier JSON                     │
   ├─────────────────────────────────────────────────┤
   │ Dossier: /home/user/documents/          ▼      │
   │                                                 │
   │ ┌─────────────────────────────────────────────┐ │
   │ │ 📄 app.got.json                             │ │
   │ │ 📄 app-fr.json                    (existant)│ │
   │ │ 📄 messages.json                            │ │
   │ └─────────────────────────────────────────────┘ │
   │                                                 │
   │ Nom: [app-fr.json                          ]   │
   │ Type: [Fichiers JSON (*.json)              ▼]  │
   │                                                 │
   │                       [Annuler] [Enregistrer]   │
   └─────────────────────────────────────────────────┘
   ```

5. **Options** :
   - **Garder le nom** : Cliquer sur "Enregistrer" → Écrase `app-fr.json`
   - **Changer le nom** : Taper `app-fr-v2.json` → Crée nouveau fichier
   - **Naviguer ailleurs** : Changer de dossier → Choisir autre emplacement

6. **Retour au dialogue principal** avec le chemin mis à jour

7. **Cliquer sur "Exporter"**

## Comparaison

### Avant (sélection manuelle)

**Avantages** :
- Simple pour les chemins déjà connus
- Tout visible dans un seul dialogue

**Inconvénients** :
- ❌ Pas de vue des fichiers existants
- ❌ Risque de fautes de frappe dans le nom
- ❌ Navigation difficile dans l'arborescence
- ❌ Pas de filtrage par type
- ❌ Interface non standard

### Après (dialogue natif)

**Avantages** :
- ✅ Interface standard et familière
- ✅ Vue des fichiers existants avec filtrage
- ✅ Navigation complète dans l'arborescence
- ✅ Autocomplétion des noms
- ✅ Moins d'erreurs de saisie
- ✅ Meilleure UX globale

**Inconvénients** :
- Nécessite un clic supplémentaire ("Parcourir...")

## Boutons Valider/Annuler

Les boutons sont bien présents et fonctionnels :

```python
# === Boutons ===
button_frame = ttk.Frame(self.dialog)
button_frame.pack(fill="x", padx=20, pady=20)

ttk.Button(button_frame, text="Annuler",
          command=self._on_cancel).pack(side="right", padx=5)

ttk.Button(button_frame, text="Exporter",
          command=self._on_export).pack(side="right", padx=5)
```

### Comportement

- **Annuler** :
  - Ferme le dialogue sans rien faire
  - Retourne `None` à `app_v2.py`
  - Aucun export n'est effectué

- **Exporter** :
  - Valide tous les champs (langue, fichier, répertoire)
  - Vérifie si le fichier existe déjà
  - Demande confirmation si nécessaire
  - Retourne la configuration d'export
  - Ferme le dialogue

## Code modifié

### Variables changées

- ~~`self.dir_var`~~ ❌ Supprimée
- ~~`self.filename_var`~~ ❌ Supprimée
- `self.output_path_var` ✅ Nouvelle (chemin complet)

### Méthodes modifiées

1. **`_create_widgets()`** :
   - Section fichier simplifiée
   - Un seul champ au lieu de deux
   - Bouton "Parcourir..." appelle `_browse_file()`

2. **`_update_default_filename()`** :
   - Construit le chemin complet
   - Met à jour `output_path_var` au lieu de `filename_var`

3. **`_browse_file()`** (nouveau) :
   - Remplace `_browse_directory()`
   - Utilise `filedialog.asksaveasfilename()`
   - Gère les filtres de types de fichiers

4. **`_on_export()`** :
   - Utilise `output_path_var`
   - Validation du chemin complet
   - Ajout automatique de l'extension `.json` si manquante

## Tests

✅ **Compilation** : `python3 -m py_compile gui/export_dialog.py` → Succès

✅ **Import** : Le module s'importe sans erreur

✅ **Intégration** : Compatible avec `app_v2.py` existant

## Résumé

Les améliorations apportées rendent le dialogue d'export beaucoup plus intuitif et professionnel :

1. ✅ **Sélecteur de fichier natif** au lieu de la saisie manuelle
2. ✅ **Filtres de types** pour voir les fichiers JSON existants
3. ✅ **Navigation complète** dans l'arborescence
4. ✅ **Boutons Valider/Annuler** bien présents et fonctionnels
5. ✅ **Validation robuste** avec vérifications multiples
6. ✅ **UX améliorée** grâce aux standards de l'OS

L'utilisateur bénéficie maintenant d'une expérience de qualité professionnelle pour l'export de ses fichiers JSON traduits !
