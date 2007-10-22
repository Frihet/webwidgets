#! /bin/bash

. Tools/pkgdisk_config.sh
. Tools/getversion.sh

if [ "$pkgdist_repository" == "tla" ]; then
 name=$(pkgdist_name)
 tla logs -f -s -D -c -r |
  while read version; read info; read summary; do
   date=$(date -d "$(echo "$info" | sed -e "s+      .*$++g")" +"%a, %d %b %Y %k:%M:%S %z")
   creator="$(echo "$info" | sed -e "s+^.*      ++g")"
   echo "$name ($(pkgdist_tlaversion2pkg "$version")) unstable; urgency=low";
   echo
   echo "  * $summary"
   echo
   echo " -- $creator  $date"
   echo
  done
elif [ "$pkgdist_repository" == "svn" ]; then
 host="$(svn info | grep URL: | sed -e "s+URL: .*://\([^/]*\)/.*+\1+g")"
 find . -type d -a ! -path "*/.svn*" -a ! -path "*/=dist*" |
  while read name; do
   svn log $name |
    tr "\n%" "%\n" |
    sed \
     -e "s+%+ ://: +g" \
     -e "s+------------------------------------------------------------------------+%+g" \
     -e "s+^% ://: ++g" |
    tr "\n%" "%\n" |
    sed \
     -e "s+ ://: \( ://: \)*+ ://: +g" \
     -e "s+^ ://: ++g" \
     -e "s+ ://: $++g" \
     -e "s+^r++g"
  done |
  sort | uniq |
  while read line; do
   version="$(echo "$line" | cut -d "|" -f 1 | sed -e "s+ *++g")"
   date=$(LC_ALL=C date -d "$(echo "$line" | cut -d "|" -f 3)" +"%a, %d %b %Y %k:%M:%S %z")
   creator="$(echo "$line" | cut -d "|" -f 2 | sed -e "s+ *++g")"
   creator="$creator <$creator@$host>"
   summary="$(
    echo "$line" |
     sed \
      -e "s+^.* ://: .* ://: ++g" \
      -e "s+ ://: + +g")"
   echo "$(pkgdist_name) ($(pkgdist_svnversion2pkg "$version")) unstable; urgency=low";
   echo
   echo "  * $summary"
   echo
   echo " -- $creator  $date"
   echo
  done
fi