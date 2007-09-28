#! /bin/sh

find . -name *.mo |
 while read name; do
  echo "Removing $name"
  rm "$name"
 done


find . -name "*.po" |
 while read name; do
  echo "Creating $(dirname "$name")/$(basename "$name" ".po").mo"
  msgfmt -o "$(dirname "$name")/$(basename "$name" ".po").mo" "$name"
 done
