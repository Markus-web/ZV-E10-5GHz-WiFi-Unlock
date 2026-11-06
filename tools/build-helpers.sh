#!/bin/sh
# clang with an ARM backend + GNU arm-none-eabi-ld; no libc required.
set -eu
cd "$(dirname "$0")"
for name in patch restore; do
  "${CLANG:-clang}" --target=arm-linux-gnueabi -c "$name.s" -o "$name.o"
  "${ARM_LD:-arm-none-eabi-ld}" -Ttext=0x10000 -e _start -o "$name.arm" "$name.o"
  rm "$name.o"
done
