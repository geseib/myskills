#!/usr/bin/env bash
# format-preview.sh — Line-numbered file viewer with indented wrapping
#
# Wraps long lines at the given width and indents continuation lines
# past the line number gutter so they don't overlap.
#
# Usage: format-preview.sh <file> [width]
#        width defaults to $FZF_PREVIEW_COLUMNS or 80

set -euo pipefail

FILE="${1:?Usage: format-preview.sh <file> [width]}"
WIDTH="${2:-${FZF_PREVIEW_COLUMNS:-80}}"

if [[ ! -f "$FILE" ]]; then
    echo "File not found: $FILE"
    exit 1
fi

awk -v w="$WIDTH" '
BEGIN {
    # Line number gutter: "  123  " = 7 chars
    gutter = 7
    pad = sprintf("%" gutter "s", "")
}
{
    # Build the full line with line number
    s = sprintf("%5d  %s", NR, $0)

    if (length(s) <= w || w <= gutter) {
        print s
        next
    }

    # First chunk: full width
    print substr(s, 1, w)
    rest = substr(s, w + 1)

    # Continuation chunks: indented past gutter
    cw = w - gutter
    if (cw < 1) cw = 1
    while (length(rest) > 0) {
        print pad substr(rest, 1, cw)
        rest = substr(rest, cw + 1)
    }
}' "$FILE"
