#! /bin/bash

. Tools/pkgdist_config.sh

disttype=deb
server=download.gna.org:/upload/webwidgets/

params=0
while (($# >> 0)); do
 case $1 in
  --disttype=*) disttype="$(echo "$1" | sed -e "s+^--disttype=++g")";;
  --upload) upload=y;;
  --server=*) server="$(echo "$1" | sed -e "s+^--server=++g")";;
  --*) help=1;;
 esac
 shift
done

if [ "$help" ]; then
 cat <<EOF
Usage: makedist.sh [--disttype=tgz|rpm|deb] [--upload [--server=UPLOAD_DIRECTORY]]

Generate and optionally upload a distribution.
Default disttype is deb.
Default UPLOAD_DIRECTORY is '$server'.
EOF
 exit 1
fi

. Tools/getversion.sh
TITLE="$(pkgdist_title)"
VENDOR="$(pkgdist_vendor)"
VERSION="$(pkgdist_version)"

echo "Building $disttype for $VERSION from $VENDOR:"

echo "Removing old files..."
rm -rf "=dist/$TITLE-$VERSION"

echo "Copying files..."
Tools/pkgdist_copy.sh "=dist/$TITLE-$VERSION"

echo "Making spec-file..."
m4 \
 -DVENDOR="$VENDOR" \
 -DVERSION="$VERSION" \
 < "Tools/$TITLE.spec.in" > "=dist/$TITLE-$VERSION/$TITLE.spec"

cd "=dist"

echo "Making tar.gz..."
tar -czf "$TITLE-$VERSION.tgz" "$TITLE-$VERSION"

case "$disttype" in
 rpm)
  echo "Building rpm..."
  rpmbuild -ta "$TITLE-$VERSION.tgz";;
 deb)
  cd $TITLE-$VERSION
  Tools/log2aptlog.sh > debian/changelog
  dpkg-buildpackage -rfakeroot
esac

if [ "$upload" ]; then
 echo "Uploading..."
 rsync -a "$server" "download/"
 case "$disttype" in
  rpm)
   bindst="$(rpm -E "%{_rpmdir}/%{_build_arch}")"
   srcdst="$(rpm -E "%{_srcrpmdir}")"
   cp "$bindst/$TITLE-$VERSION-1_ti_1.i386.rpm" "download/RPMS"
   cp "$bindst/$TITLE-"*"-$VERSION-1_ti_1.i386.rpm" "download/RPMS"
   cp "$srcdst/$TITLE-$VERSION-1_ti_1.src.rpm" "download/RPMS"
   yum-arch "download/RPMS"
   createrepo "download/RPMS"
   ;;
  tgz)
   cp "$TITLE-$VERSION.tgz" "download/$TITLE-$VERSION.tgz"
   ;;
 esac
 rsync -a "download/" "$server"
fi
