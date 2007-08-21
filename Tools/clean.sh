#! /bin/sh

{
 tla inventory -f -p
 tla inventory -d -p
 tla inventory -f -b
 tla inventory -d -b
 tla inventory -f -j
 tla inventory -d -j
} |
 while read name; do
  echo "Removing '$name'"
  rm -rf "$name"
 done

rm -rf {arch}/++pristine-trees
