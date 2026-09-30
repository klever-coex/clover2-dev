# Build ros2-jazzy-custom metapackage
#
# Usage:
#   make           — build .deb
#   make clean     — remove build artifacts

DEB := $(shell ls ../*.deb 2>/dev/null)

.PHONY: all clean

all:
	dpkg-buildpackage -us -uc -b

clean:
	rm -rf debian/.debhelper debian/ros2-jazzy-custom *.deb *.buildinfo *.changes
