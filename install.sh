#!/bin/sh

RESET="\e[0m"
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
CYAN="\e[36m"

echo -e "${YELLOW}Welcome to CullaBox ----------------------------------" 
echo -e "${BLUE}I will try to compile a helper program. You need the"
echo -e "development packages of libX11 and libjpeg(-turbo)."

gcc getbg.c -o getbg -lX11 -ljpeg 2>/dev/null

if [ $? != 0 ]; then
    echo -e "${RED}Compilation failed. Please check installed packages.${RESET}"
    exit 1
fi

echo -e "${GREEN}Good, the helper compiled.\n"
echo -e "${BLUE}Now I'll check for Python Pillow"

python3 -c "from PIL import Image" 2>/dev/null

if [ $? != 0 ]; then
    echo -e "${RED}Pillow was not found. Use your package manager or try"
    echo -e "'pip install Pillow'.${RESET}"
    exit 1
fi

echo -e "${GREEN}Good, Pillow is installed.\n${RESET}"

BINDIR=$HOME/.local/bin

if [ ! -d $BINDIR ]; then
    mkdir -p $BINDIR
fi

echo -e "${CYAN}Copying executables to $BINDIR.${RESET}"
cp CullaBox.py $BINDIR
chmod 755 $BINDIR/CullaBox.py
mv getbg $BINDIR

ASSETS=$HOME/.local/share/CullaBox

if [ ! -d $ASSETS ]; then
    mkdir -p $ASSETS
fi

echo -e "${CYAN}Copying CullaBox assets base.${RESET}"
cp -vf themerc tint2rc $ASSETS

OBOXTHEME=$HOME/.themes

if [ ! -d $OBOXTHEME ]; then
    mkdir -p $OBOXTHEME
fi

echo -e "${CYAN}Copying OpenBox theme.${RESET}"
cp -R CullaBox $OBOXTHEME

QT5CT=$HOME/.config/qt5ct/colors

if [ ! -d $QT5CT ]; then
    mkdir -p $QT5CT
fi

echo -e "${CYAN}Copying Qt5ct colors.${RESET}"
cp CullaBox.conf $QT5CT
