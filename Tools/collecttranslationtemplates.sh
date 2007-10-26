#! /bin/sh

mkdir -p translations
msgcat --sort-output $(find . -name *.pot) > translations/Webwidgets.pot

