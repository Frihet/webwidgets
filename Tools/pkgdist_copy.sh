#! /bin/bash

. Tools/pkgdist_config.sh

dstpath="$1"

if [ "$pkgdist_repository" == "tla" ]; then
 {
  echo "."
  tla inventory -s -d
 } |
  sed -e "s+(sp)+ +g" |
  while read dir; do
   mkdir -p "$dstpath/$dir"
   cp -a "$dir/.arch-ids" "$dstpath/$dir/.arch-ids"
  done

 tla inventory -s -f |
  sed -e "s+(sp)+ +g" |
  while read file; do
   cp -d "$file" "$dstpath/$file"
  done

 mkdir -p "$dstpath/{arch}"
 find "{arch}" -maxdepth 1 -mindepth 1 ! -name "++pristine-trees" |
  while read file; do
   cp -a -d "$file" "$dstpath/$file"
  done
elif [ "$pkgdist_repository" == "svn" ]; then
 mkdir -p "$dstpath"
 cp -a ".svn" "$dstpath/.svn"
 svn ls -R |
  while read path; do
   if [ -d "$path" ]; then
    mkdir -p "$dstpath/$path"
    cp -a "$path/.svn" "$dstpath/$path/.svn"
   else
    cp -a "$path" "$dstpath/$path"
   fi
  done
fi
