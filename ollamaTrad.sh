#!/bin/bash
# OllamaTrad Launcher Script for Linux
# Version: 3.0

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher le logo
show_logo() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║                                           ║"
    echo "║           🤖 OllamaTrad v3.0              ║"
    echo "║   Intelligent JSON Translation System     ║"
    echo "║                                           ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonction pour vérifier Python
check_python() {
    echo -e "${YELLOW}🔍 Vérification de Python...${NC}"

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        echo -e "${GREEN}✅ Python trouvé: $PYTHON_VERSION${NC}"
        return 0
    elif command -v python &> /dev/null; then
        # Vérifier que c'est Python 3
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
            PYTHON_CMD="python"
            echo -e "${GREEN}✅ Python trouvé: $PYTHON_VERSION${NC}"
            return 0
        fi
    fi

    echo -e "${RED}❌ Python 3 n'est pas installé!${NC}"
    echo -e "${YELLOW}📦 Installation requise:${NC}"
    echo "   sudo apt install python3 python3-tk  # Debian/Ubuntu"
    echo "   sudo dnf install python3 python3-tkinter  # Fedora"
    echo "   sudo pacman -S python python-tk  # Arch Linux"
    return 1
}

# Fonction pour vérifier les dépendances
check_dependencies() {
    echo -e "${YELLOW}🔍 Vérification des dépendances...${NC}"

    # Vérifier tkinter
    if ! $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
        echo -e "${RED}❌ tkinter n'est pas installé!${NC}"
        echo -e "${YELLOW}📦 Installation requise:${NC}"
        echo "   sudo apt install python3-tk  # Debian/Ubuntu"
        echo "   sudo dnf install python3-tkinter  # Fedora"
        return 1
    fi

    # Vérifier les autres dépendances
    MISSING_DEPS=()

    for dep in json5 requests aiohttp; do
        if ! $PYTHON_CMD -c "import $dep" 2>/dev/null; then
            MISSING_DEPS+=($dep)
        fi
    done

    if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
        echo -e "${YELLOW}📦 Installation des dépendances manquantes...${NC}"
        $PYTHON_CMD -m pip install --user "${MISSING_DEPS[@]}"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Dépendances installées avec succès${NC}"
        else
            echo -e "${RED}❌ Erreur lors de l'installation des dépendances${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ Toutes les dépendances sont installées${NC}"
    fi

    return 0
}

# Fonction pour lancer l'application
launch_app() {
    echo -e "${BLUE}🚀 Lancement d'OllamaTrad...${NC}"

    # Se placer dans le répertoire du script
    cd "$(dirname "$0")"

    # Lancer l'application en mode GUI
    $PYTHON_CMD ollamaTrad.py --gui "$@"

    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ L'application s'est terminée avec une erreur (code: $EXIT_CODE)${NC}"
        echo -e "${YELLOW}💡 Consultez les messages d'erreur ci-dessus pour plus d'informations${NC}"
        read -p "Appuyez sur Entrée pour fermer..."
        return $EXIT_CODE
    fi

    return 0
}

# Programme principal
main() {
    show_logo

    # Vérifier Python
    if ! check_python; then
        read -p "Appuyez sur Entrée pour fermer..."
        exit 1
    fi

    # Vérifier les dépendances
    if ! check_dependencies; then
        read -p "Appuyez sur Entrée pour fermer..."
        exit 1
    fi

    # Lancer l'application
    launch_app "$@"

    exit $?
}

# Exécution
main "$@"
