#! /bin/sh

find . -name "*.pot" | grep -v "./translations" |
 while read potfile; do
  find translations -name "*.po" |
   while read pofile; do
    lang="$(basename "$(dirname "$(dirname "$pofile")")")"
    domain="$(basename "$pofile")"
    dstdir="$(dirname "$potfile")/$lang/LC_MESSAGES"
    mkdir -p "$dstdir"
    msgmerge --no-fuzzy-matching --sort-output "$pofile" "$potfile" |
     grep -v -e "^#~" > "$dstdir/$domain"
   done
 done
