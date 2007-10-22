#! /bin/bash

. Tools/pkgdisk_config.sh

if [ "$pkgdist_repository" == "tla" ]; then
 pkgdist_title () { tla tree-version | sed -e "s+.*/\(.*\)--.*--.*+\1+g"; }
 pkgdist_name () { pkgdist_title | tr "A-Z" "a-z"; }
 pkgdist_vendor () { tla logs -f -r | head -1 | sed -e "s+/.*$++g"; }
 pkgdist_version () { pkgdist_tlaversion2pkg "$(tla logs -f -r | head -1)"; }

 pkgdist_tlaversion2pkg () {
  tlaversion="$1"
  if [ "$(echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\1+g")" == "release" ]; then
   echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\2.\3+g"
  else
   echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\2.\1.\3+g"
  fi
 }
elif [ "$pkgdist_repository" == "svn" ]; then
 pkgdist_title () {
  pkgdist_svn_versionpath |
   sed \
    -e "s+.*/\([^/]*\)/trunk+\1+g" \
    -e "s+.*/\([^/]*\)/branches/[^/]*+\1+g" \
    -e "s+.*/\([^/]*\)/tags/[^/]*+\1+g"
 }
 pkgdist_name () { pkgdist_title | tr "A-Z" "a-z"; }
 pkgdist_vendor () { echo $pkgdist_vendor; }
 pkgdist_version () {
  pkgdist_svnversion2pkg $(
    svn info |
     grep Revision: |
     sed -e "s+.*Revision: \(.*\)+\1+g"
  )
 }

 pkgdist_svnversion2pkg () {
  echo $(
   pkgdist_svn_versionpath |
    sed \
     -e "s+.*/\(trunk\)+\1+g" \
     -e "s+.*/branches/\([^/]*\)+branch.\1+g" \
     -e "s+.*/tags/\([^/]*\)+tag.\1+g"
   ).$1
 }

 pkgdist_svn_versionpath () {
  svn info |
   grep URL: |
   sed -e "s+.*URL: .*://[^/]*/\(.*\)+\1+g"
 }
fi
