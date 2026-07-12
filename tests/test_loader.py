# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Tests for the pain001-loader-mt101 loader."""

from __future__ import annotations

import pytest
from pain001.validation.schema_validator import SchemaValidator

from pain001_loader_mt101 import __version__, parse_mt101

# Target ISO 20022 message type for the flat records produced here.
PAIN001_MESSAGE_TYPE = "pain.001.001.09"


def _single_mt101() -> str:
    """A complete single-transaction MT101 covering every mapped field.

    Ordering customer (:50K:) and account-servicing institution (:52A:)
    live in sequence A; the one transaction lives in sequence B.
    """
    return (
        ":20:MSGREF001\n"
        ":30:260712\n"
        ":50K:/DE89370400440532013000\n"
        "JOHN DOE\n"
        "123 MAIN STREET\n"
        "BERLIN\n"
        ":52A:DEUTDEFF\n"
        ":21:TXN-0001\n"
        ":32B:EUR12345,67\n"
        ":57A:CHASUS33\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        "1 CORPORATE AVENUE\n"
        "LONDON\n"
        ":70:INVOICE 998877\n"
        ":71A:SHA\n"
    )


def _multi_mt101() -> str:
    """A two-transaction MT101 with shared sequence-A debtor fields."""
    return (
        ":20:MSGREF2026070901\n"
        ":21R:CUSTREF-A\n"
        ":50H:/DE89370400440532013000\n"
        "GLOBAL IMPORTS GMBH\n"
        "100 HAFEN STRASSE\n"
        "HAMBURG\n"
        ":52A:DEUTDEFF\n"
        ":30:260712\n"
        ":21:TXN-REF-0001\n"
        ":32B:EUR12345,67\n"
        ":57A:CHASUS33\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        "1 CORPORATE AVENUE\n"
        "LONDON\n"
        ":70:INVOICE 998877\n"
        ":71A:SHA\n"
        ":21:TXN-REF-0002\n"
        ":32B:USD5000,00\n"
        ":57A:BOFAUS3N\n"
        ":59:/FR1420041010050500013M02606\n"
        "LES FLEURS SARL\n"
        ":70:CONTRACT 445566\n"
        ":71A:OUR\n"
    )


def test_version_exposed() -> None:
    """The package exposes a non-empty semantic-style version string."""
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2


def test_single_mt101_maps_every_field() -> None:
    """A complete single-transaction MT101 maps to a full pain.001 record."""
    (record,) = parse_mt101(_single_mt101())
    assert record == {
        "id": "MSGREF001",
        "date": "2026-07-12",
        "nb_of_txs": 1,
        "ctrl_sum": 12345.67,
        "payment_information_id": "MSGREF001",
        "payment_method": "TRF",
        "batch_booking": False,
        "service_level_code": "SEPA",
        "requested_execution_date": "2026-07-12",
        "charge_bearer": "SHAR",
        "payment_id": "TXN-0001",
        "payment_amount": 12345.67,
        "currency": "EUR",
        "creditor_name": "ACME TRADING LTD",
        "remittance_information": "INVOICE 998877",
        "initiator_name": "JOHN DOE",
        "debtor_name": "JOHN DOE",
        "debtor_account_IBAN": "DE89370400440532013000",
        "debtor_agent_BIC": "DEUTDEFF",
        "creditor_agent_BIC": "CHASUS33",
        "creditor_account_IBAN": "GB29NWBK60161331926819",
    }


def test_records_validate_against_pain001_schema() -> None:
    """The KEY correctness proof: records are schema-valid pain.001 rows.

    Runs the real :class:`SchemaValidator` for ``pain.001.001.09`` from the
    ``pain001`` library over the parsed multi-transaction records.
    """
    records = parse_mt101(_multi_mt101())
    validator = SchemaValidator(PAIN001_MESSAGE_TYPE)
    total, valid, errors = validator.validate_batch(records)
    assert total == 2
    assert valid == 2
    assert errors == []


def test_single_record_also_validates() -> None:
    """A single-transaction MT101 also yields a schema-valid record."""
    records = parse_mt101(_single_mt101())
    validator = SchemaValidator(PAIN001_MESSAGE_TYPE)
    total, valid, errors = validator.validate_batch(records)
    assert (total, valid, errors) == (1, 1, [])


def test_returns_one_record_per_transaction() -> None:
    """An MT101 with two sequence-B blocks yields two records."""
    records = parse_mt101(_multi_mt101())
    assert isinstance(records, list)
    assert len(records) == 2
    assert [r["payment_id"] for r in records] == ["TXN-REF-0001", "TXN-REF-0002"]


def test_nb_of_txs_counts_sequence_b_blocks() -> None:
    """nb_of_txs is the count of sequence-B blocks, repeated per record."""
    records = parse_mt101(_multi_mt101())
    assert all(r["nb_of_txs"] == 2 for r in records)


def test_ctrl_sum_totals_all_transaction_amounts() -> None:
    """ctrl_sum is the sum of every transaction amount, repeated per record."""
    records = parse_mt101(_multi_mt101())
    assert all(r["ctrl_sum"] == 17345.67 for r in records)


def test_per_transaction_amounts_and_currencies() -> None:
    """Each record carries its own :32B: amount and currency."""
    first, second = parse_mt101(_multi_mt101())
    assert (first["payment_amount"], first["currency"]) == (12345.67, "EUR")
    assert (second["payment_amount"], second["currency"]) == (5000.0, "USD")


def test_sequence_a_debtor_applies_to_every_transaction() -> None:
    """Sequence-A ordering customer / servicing bank flow to all records."""
    for record in parse_mt101(_multi_mt101()):
        assert record["debtor_name"] == "GLOBAL IMPORTS GMBH"
        assert record["debtor_account_IBAN"] == "DE89370400440532013000"
        assert record["debtor_agent_BIC"] == "DEUTDEFF"
        assert record["initiator_name"] == "GLOBAL IMPORTS GMBH"


def test_sequence_b_overrides_sequence_a_party_fields() -> None:
    """A sequence-B :50a:/:52a: overrides the sequence-A value."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":50K:/DE00000000000000000000\n"
        "SEQ A CUSTOMER\n"
        ":52A:AAAAAAAA\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":50K:/GB29NWBK60161331926819\n"
        "BLOCK CUSTOMER\n"
        ":52A:BBBBBBBB\n"
        ":57A:CHASUS33\n"
        ":59:/GB29NWBK60161331926819\n"
        "BENEFICIARY LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["debtor_name"] == "BLOCK CUSTOMER"
    assert record["debtor_agent_BIC"] == "BBBBBBBB"
    assert record["debtor_account_IBAN"] == "GB29NWBK60161331926819"


@pytest.mark.parametrize(
    ("swift_code", "pain_code"),
    [("OUR", "DEBT"), ("BEN", "CRED"), ("SHA", "SHAR")],
)
def test_charge_bearer_mapping(swift_code: str, pain_code: str) -> None:
    """:71A: OUR/BEN/SHA map to DEBT/CRED/SHAR."""
    mt101 = _single_mt101().replace(":71A:SHA", f":71A:{swift_code}")
    (record,) = parse_mt101(mt101)
    assert record["charge_bearer"] == pain_code


def test_unknown_charge_code_defaults_to_slev() -> None:
    """An unrecognised :71A: code falls back to the SLEV default."""
    mt101 = _single_mt101().replace(":71A:SHA", ":71A:ZZZ")
    (record,) = parse_mt101(mt101)
    assert record["charge_bearer"] == "SLEV"


def test_missing_charge_field_defaults_to_slev() -> None:
    """No :71A: at all falls back to the SLEV default (schema requires one)."""
    mt101 = _single_mt101().replace(":71A:SHA\n", "")
    (record,) = parse_mt101(mt101)
    assert record["charge_bearer"] == "SLEV"


def test_swift_decimal_comma_is_parsed() -> None:
    """The SWIFT comma decimal separator becomes a float."""
    mt101 = _single_mt101().replace(":32B:EUR12345,67", ":32B:USD1000,50")
    (record,) = parse_mt101(mt101)
    assert record["payment_amount"] == 1000.50
    assert record["currency"] == "USD"


def test_trailing_comma_amount_is_whole_number() -> None:
    """A trailing comma (no decimals) yields a whole amount."""
    mt101 = _single_mt101().replace(":32B:EUR12345,67", ":32B:EUR250,")
    (record,) = parse_mt101(mt101)
    assert record["payment_amount"] == 250.0


def test_execution_date_maps_to_both_date_fields() -> None:
    """:30: populates both date and requested_execution_date (YYYY-MM-DD)."""
    (record,) = parse_mt101(_single_mt101())
    assert record["date"] == "2026-07-12"
    assert record["requested_execution_date"] == "2026-07-12"


def test_sliding_year_window_maps_old_dates_to_1900s() -> None:
    """A YY >= 80 execution date maps to the 1900s."""
    mt101 = _single_mt101().replace(":30:260712", ":30:950712")
    (record,) = parse_mt101(mt101)
    assert record["date"] == "1995-07-12"


def test_malformed_execution_date_raises() -> None:
    """A malformed :30: value raises ValueError mentioning :30:."""
    mt101 = _single_mt101().replace(":30:260712", ":30:JUL2026")
    with pytest.raises(ValueError, match=":30:"):
        parse_mt101(mt101)


def test_50k_name_extraction_skips_account_line() -> None:
    """:50K: name extraction returns the name, not the leading /account."""
    (record,) = parse_mt101(_single_mt101())
    assert record["debtor_name"] == "JOHN DOE"
    assert record["debtor_account_IBAN"] == "DE89370400440532013000"


def test_59_beneficiary_name_and_account_extraction() -> None:
    """:59: beneficiary yields the name and the IBAN account."""
    (record,) = parse_mt101(_single_mt101())
    assert record["creditor_name"] == "ACME TRADING LTD"
    assert record["creditor_account_IBAN"] == "GB29NWBK60161331926819"


def test_option_f_structured_name_uses_subfield_1() -> None:
    """Option F (structured) party name is taken from the ``1/`` sub-field."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":50F:/DE89370400440532013000\n"
        "1/ALICE EXAMPLE\n"
        "2/10 DOWNING STREET\n"
        "3/GB/LONDON\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59F:/GB29NWBK60161331926819\n"
        "1/BOB BENEFICIARY\n"
        "2/1 CORPORATE AVENUE\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["debtor_name"] == "ALICE EXAMPLE"
    assert record["creditor_name"] == "BOB BENEFICIARY"


def test_option_f_without_subfield_1_falls_back_to_first_line() -> None:
    """A structured field lacking a ``1/`` line falls back to its first line."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59F:/GB29NWBK60161331926819\n"
        "3/GB/LONDON\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["creditor_name"] == "3/GB/LONDON"


def test_option_a_beneficiary_uses_bic_as_name() -> None:
    """Option A beneficiary (account + BIC) uses the BIC as the name."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59A:/GB29NWBK60161331926819\n"
        "CHASUS33\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["creditor_name"] == "CHASUS33"


def test_11_char_bic_is_accepted() -> None:
    """An 11-character BIC (with branch code) is extracted intact."""
    mt101 = _single_mt101().replace(":52A:DEUTDEFF", ":52A:DEUTDEFF500")
    (record,) = parse_mt101(mt101)
    assert record["debtor_agent_BIC"] == "DEUTDEFF500"


def test_option_d_institution_without_bic_omits_agent() -> None:
    """Option D (name/address) without a BIC leaves the agent BIC unset."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":52D:BANK OF SOMEWHERE\n"
        "1 BANK STREET\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":57D:ANOTHER BANK\n"
        "2 BANK ROAD\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert "debtor_agent_BIC" not in record
    assert "creditor_agent_BIC" not in record


def test_missing_institutions_omit_agents() -> None:
    """No :52a:/:57a: fields at all leaves both agent BICs unset."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":50K:/DE89370400440532013000\n"
        "JOHN DOE\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert "debtor_agent_BIC" not in record
    assert "creditor_agent_BIC" not in record


def test_ordering_customer_account_only_omits_debtor_name() -> None:
    """A :50K: with only an account line leaves debtor/initiator name unset."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":50K:/DE89370400440532013000\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert "debtor_name" not in record
    assert "initiator_name" not in record
    assert record["debtor_account_IBAN"] == "DE89370400440532013000"


def test_ordering_customer_name_only_omits_account() -> None:
    """A :50K: with a name but no account line leaves the IBAN unset."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":50K:JOHN DOE\n"
        "123 MAIN STREET\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["debtor_name"] == "JOHN DOE"
    assert "debtor_account_IBAN" not in record


def test_missing_ordering_customer_omits_debtor_fields() -> None:
    """No :50a: at all leaves debtor name/account/initiator unset."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        ":71A:OUR\n"
    )
    (record,) = parse_mt101(mt101)
    assert "debtor_name" not in record
    assert "debtor_account_IBAN" not in record
    assert "initiator_name" not in record


def test_missing_remittance_defaults_to_notprovided() -> None:
    """No :70: falls back to the NOTPROVIDED sentinel (schema requires one)."""
    mt101 = _single_mt101().replace(":70:INVOICE 998877\n", "")
    (record,) = parse_mt101(mt101)
    assert record["remittance_information"] == "NOTPROVIDED"


def test_multiline_remittance_is_whitespace_collapsed() -> None:
    """A multi-line :70: is collapsed to a single whitespace-normalised line."""
    mt101 = _single_mt101().replace(
        ":70:INVOICE 998877\n", ":70:INVOICE 998877\nPO 12345\n"
    )
    (record,) = parse_mt101(mt101)
    assert record["remittance_information"] == "INVOICE 998877 PO 12345"


def test_long_remittance_is_capped_at_140_chars() -> None:
    """Remittance longer than 140 chars is truncated to the schema maximum."""
    long_text = "X" * 200
    mt101 = _single_mt101().replace(":70:INVOICE 998877", f":70:{long_text}")
    (record,) = parse_mt101(mt101)
    assert len(record["remittance_information"]) == 140


def test_raw_block4_envelope_is_unwrapped() -> None:
    """A raw ``{4:...-}`` SWIFT block-4 envelope is parsed transparently."""
    inner = _single_mt101()
    wrapped = "{1:F01DEUTDEFFAXXX0000000000}{2:I101CHASUS33XXXXN}{4:\n" + inner + "-}"
    (record,) = parse_mt101(wrapped)
    assert record["id"] == "MSGREF001"
    assert record["charge_bearer"] == "SHAR"


def test_missing_sender_reference_raises() -> None:
    """A payload without :20: raises ValueError mentioning :20:."""
    mt101 = _single_mt101().replace(":20:MSGREF001\n", "")
    with pytest.raises(ValueError, match=":20:"):
        parse_mt101(mt101)


def test_empty_sender_reference_raises() -> None:
    """A :20: with an empty value raises (id is required)."""
    mt101 = _single_mt101().replace(":20:MSGREF001", ":20:")
    with pytest.raises(ValueError, match=":20:"):
        parse_mt101(mt101)


def test_missing_execution_date_raises() -> None:
    """A payload without :30: raises ValueError mentioning :30:."""
    mt101 = _single_mt101().replace(":30:260712\n", "")
    with pytest.raises(ValueError, match=":30:"):
        parse_mt101(mt101)


def test_no_transaction_raises() -> None:
    """A payload with no sequence-B :21: raises ValueError."""
    mt101 = ":20:REF\n:30:260712\n:50K:/DE89370400440532013000\nJOHN DOE\n"
    with pytest.raises(ValueError, match="no transaction"):
        parse_mt101(mt101)


def test_empty_transaction_reference_raises() -> None:
    """A sequence-B block with an empty :21: reference raises."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
    )
    with pytest.raises(ValueError, match=":21:"):
        parse_mt101(mt101)


def test_missing_amount_raises() -> None:
    """A transaction without :32B: raises ValueError mentioning :32B:."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
    )
    with pytest.raises(ValueError, match=":32B:"):
        parse_mt101(mt101)


def test_malformed_amount_raises() -> None:
    """A malformed :32B: value raises ValueError mentioning :32B:."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":32B:GARBAGE\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
    )
    with pytest.raises(ValueError, match=":32B:"):
        parse_mt101(mt101)


def test_missing_beneficiary_raises() -> None:
    """A transaction with no :59:/:59A:/:59F: raises ValueError."""
    mt101 = ":20:REF\n:30:260712\n:21:TXN1\n:32B:EUR100,00\n:71A:OUR\n"
    with pytest.raises(ValueError, match="beneficiary"):
        parse_mt101(mt101)


def test_beneficiary_without_name_raises() -> None:
    """A beneficiary field carrying only an account (no name) raises."""
    mt101 = (
        ":20:REF\n"
        ":30:260712\n"
        ":21:TXN1\n"
        ":32B:EUR100,00\n"
        ":59:/GB29NWBK60161331926819\n"
        ":71A:OUR\n"
    )
    with pytest.raises(ValueError, match="no name"):
        parse_mt101(mt101)
