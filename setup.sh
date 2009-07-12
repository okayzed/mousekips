#!/usr/env /bin/sh
SHOW_BLOCK_HINT=1
FONT_SIZE="25"
FONT_NAME="monospace"
LAYOUT="[qwertyuiop,\
                QWERTYUIOP,\
                asdfghjkl;,\
                ASDFGHJKL:,\
                zxcvbnm\,./,\
                ZXCVBNM<>?]"
LAUNCH="<Control><Shift>a"
gconftool -s --type string "/apps/mousekips/launch" "$LAUNCH"
gconftool -s --type list --list-type string /apps/mousekips/layout "$LAYOUT"
gconftool -s --type int "/apps/mousekips/font_size" "$FONT_SIZE"
gconftool -s --type string "/apps/mousekips/font_name" "$FONT_NAME"
gconftool -s --type bool "/apps/mousekips/block_hint" "$SHOW_BLOCK_HINT"
