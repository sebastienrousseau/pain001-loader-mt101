# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Parse an MT101 and validate the records against the real pain.001 schema.

This proves the round trip: MT101 text in, schema-valid ``pain.001.001.09``
flat records out, verified by the ``pain001`` library's ``SchemaValidator``.

Run with ``python examples/02_validate_against_pain001.py``.
"""

from pain001.validation.schema_validator import SchemaValidator

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
    """Parse the demo MT101 and validate it against pain.001.001.09."""
    records = parse_mt101(MT101)
    validator = SchemaValidator("pain.001.001.09")
    total, valid, errors = validator.validate_batch(records)
    print(f"records: {total}  valid: {valid}")
    if errors:
        for index, row_errors in errors:
            for error in row_errors:
                print(f"  row {index}: {error}")
    else:
        print("All records are schema-valid pain.001.001.09.")


if __name__ == "__main__":
    main()
