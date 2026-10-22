# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered with `make demo` (VHS, https://github.com/charmbracelet/vhs)
# from a virtual environment where the package is installed. Runs the
# repository's own example against the MT101 text it ships; no network.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 680
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type `sed -n '/^MT101 = /,/^"""$/p' examples/01_minimal_parse.py | head -12`
Enter
Sleep 3s

Type "python examples/01_minimal_parse.py | head -18"
Enter
Sleep 4s

Type "printf ':20:REF\n:30:260230\n:21:T1\n:32B:EUR100,\n:59:ACME\n' | python -c 'import sys; from pain001_loader_mt101 import parse_mt101; parse_mt101(sys.stdin.read())' 2>&1 | tail -1"
Enter
Sleep 5s
