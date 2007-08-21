#! /bin/sh

pkgdist_title () { tla tree-version | sed -e "s+.*/\(.*\)--.*--.*+\1+g"; }
pkgdist_name () { pkgdist_title | tr "A-Z" "a-z"; }
pkgdist_vendor () { tla logs -f -r | head -1 | sed -e "s+/.*$++g"; }
pkgdist_version () { tlaversion2pkg "$(tla logs -f -r | head -1)"; }

tlaversion2pkg () {
 tlaversion="$1"
 if [ "$(echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\1+g")" == "release" ]; then
  echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\2.\3+g"
 else
  echo "$tlaversion" | sed -e "s+^.*--\(.*\)--\([0-9.]*\)--.*-\([0-9]*\)$+\2.\1.\3+g"
 fi
}
