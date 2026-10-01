#!/bin/sh
# Build libtihl.so: TilEm 2.0 emulator core + headless harness shim.
set -e
cd "$(dirname "$0")"
EMU=../vendor/tilem-2.0/emu
SRCS="$(ls $EMU/*.c) $(ls $EMU/x*/*.c) tihl.c"
gcc -O2 -DHAVE_CONFIG_H -fPIC -shared -w -I. -I$EMU -o libtihl.so $SRCS
echo built libtihl.so
