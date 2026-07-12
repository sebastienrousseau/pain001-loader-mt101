# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Minimal example: parse an MT101 payload and inspect the flat records.

Run with ``python examples/01_minimal_parse.py``.
"""

from pain001_loader_mt101 import parse_mt101

MT101 = """:20:MSGREF2026070901
:21R:CUSTREF-A
:50H:/DE89370400440532013000
GLOBAL IMPORTS GMBH
100 HAFEN STRASSE
HAMBURG
:52A:DEUTDEFF
:30:260712
:21:TXN-REF-0001
:32B:EUR12345,67
:57A:CHASUS33
:59:/GB29NWBK60161331926819
ACME TRADING LTD
1 CORPORATE AVENUE
LONDON
:70:INVOICE 998877
:71A:SHA
:21:TXN-REF-0002
:32B:USD5000,00
:57A:BOFAUS3N
:59:/FR1420041010050500013M02606
LES FLEURS SARL
:70:CONTRACT 445566
:71A:OUR
"""


def main() -> None:
    """Parse the demo MT101 and print each resulting pain.001 record."""
    records = parse_mt101(MT101)
    print(f"{len(records)} transaction(s) parsed\n")
    for index, record in enumerate(records, start=1):
        print(f"--- transaction {index} ---")
        for key, value in record.items():
            print(f"{key:24}: {value!r}")
        print()


if __name__ == "__main__":
    main()
