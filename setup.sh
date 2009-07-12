#!/usr/env /bin/sh

LAYOUT_STRING="[qwertyuiop,\
                QWERTYUIOP,\
                asdfghjkl;,\
                ASDFGHJKL:,\
                zxcvbnm\,./,\
                ZXCVBNM<>?]"
LAUNCH_STRING="<Control><Shift>a"
gconftool -s --type string "/apps/mousekips/launch" "$LAUNCH_STRING"
gconftool -s --type list --list-type string /apps/mousekips/layout "$LAYOUT_STRING"

