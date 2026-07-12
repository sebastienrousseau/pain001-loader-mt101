# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""SWIFT MT101 -> ISO 20022 pain.001 loader for the pain001 suite.

SWIFT MT101 (*Request for Transfer*) is the legacy message an account
owner sends to instruct one or more credit transfers, and that ISO 20022
``pain.001`` (Customer Credit Transfer Initiation) replaces under the
CBPR+ migration. This package bridges that gap: pass an MT101 text
payload to :func:`parse_mt101` and get back the flat records that the
:mod:`pain001` library validates against the ``pain.001.001.09`` schema
and turns into pain.001 XML. An MT101 can carry several transactions, so
one record is returned per transaction.
"""

from pain001_loader_mt101.loader import parse_mt101

__version__ = "0.0.1"

__all__ = ["parse_mt101", "__version__"]
