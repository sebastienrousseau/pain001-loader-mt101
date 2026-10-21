# SPDX-License-Identifier: Apache-2.0 OR MIT
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


# Record keys that identify a person or an account. A real MT101 carries
# real names and IBANs, so the example names these keys and redacts their
# values instead of printing them, the way a log line should.
PARTY_KEYS = frozenset(
    {
        "initiator_name",
        "debtor_name",
        "debtor_account_IBAN",
        "debtor_agent_BIC",
        "creditor_name",
        "creditor_account_IBAN",
        "creditor_agent_BIC",
    }
)


def main() -> None:
    """Parse the demo MT101 and print each pain.001 record, parties redacted."""
    records = parse_mt101(MT101)
    print(f"{len(records)} transaction(s) parsed\n")
    for index, record in enumerate(records, start=1):
        print(f"--- transaction {index} ---")
        print(f"{'id':24}: {record['id']!r}")
        print(
            f"{'requested_execution_date':24}: {record['requested_execution_date']!r}"
        )
        print(f"{'payment_id':24}: {record['payment_id']!r}")
        print(f"{'payment_amount':24}: {record['payment_amount']!r}")
        print(f"{'currency':24}: {record['currency']!r}")
        print(f"{'charge_bearer':24}: {record['charge_bearer']!r}")
        print(f"{'remittance_information':24}: {record['remittance_information']!r}")
        print(f"{'nb_of_txs':24}: {record['nb_of_txs']!r}")
        print(f"{'ctrl_sum':24}: {record['ctrl_sum']!r}")
        for key in sorted(PARTY_KEYS & record.keys()):
            print(f"{key:24}: <redacted>")
        print()


if __name__ == "__main__":
    main()
