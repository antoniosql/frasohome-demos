"""Pruebas de las reglas de limpieza con los casos sucios reales de datos/."""
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import limpieza as L  # noqa: E402


@pytest.mark.parametrize("raw, expected", [
    ("2025-05-11 15:46:46", datetime(2025, 5, 11, 15, 46, 46)),
    ("13/12/25 11:42", datetime(2025, 12, 13, 11, 42)),
    ("23/12/2018", datetime(2018, 12, 23)),
    ("2020/09/30", datetime(2020, 9, 30)),
    ("14 de septiembre de 2025 08:25", datetime(2025, 9, 14, 8, 25)),
    ("10 de Enero de 2019", datetime(2019, 1, 10)),
    ("07-06-86", datetime(1986, 6, 7)),          # año con dos cifras en el pasado
    ("15-12-24", datetime(2024, 12, 15)),
    ("31/02/1990", None), ("2026-13-01", None), ("2025-13-40", None), ("", None), ("N/A", None),
])
def test_parse_datetime(raw, expected):
    assert L.parse_datetime(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2025-04", "2025-04"), ("2025/04", "2025-04"), ("01/2026", "2026-01"), ("13/2026", None), ("abc", None),
])
def test_parse_month(raw, expected):
    assert L.parse_month(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("221.99", 221.99), ("103,00", 103.0), ("€848.91", 848.91), ("1,136.08", 1136.08), ("€1.136,08", 1136.08),
    ("12.5 EUR", 12.5), ("40 €", 40.0), ("92,4%", 92.4), ("-7,67", -7.67), ("€-15.13", -15.13),
    ("100,0,0", None), ("abc", None), ("", None),
])
def test_parse_number(raw, expected):
    assert L.parse_number(raw) == expected


@pytest.mark.parametrize("fn, raw, expected", [
    (L.customer_id, "c0077", ("C0077", True)), (L.customer_id, " C0012", ("C0012", True)),
    (L.customer_id, "C-0010", ("C0010", True)), (L.customer_id, "CL0002", ("C0002", True)),
    (L.customer_id, "GUEST", (None, False)), (L.customer_id, "CX123", (None, False)), (L.customer_id, "NULL", (None, True)),
    (L.product_id, "p1005", ("P1005", True)), (L.product_id, "SKU-1019", ("P1019", True)),
    (L.product_id, "PX1004", ("P1004", True)), (L.product_id, "P10O5", ("P1005", True)),
    (L.product_id, "P101Z", (None, False)), (L.product_id, "p10X1", (None, False)),
    (L.store_id, "s1", ("S001", True)), (L.store_id, "S01", ("S001", True)), (L.store_id, " ONLINE", ("ONLINE", True)),
    (L.store_id, "??", (None, True)),
    (L.ticket_id, "500031", ("T-500031", True)), (L.ticket_id, "T500540", ("T-500540", True)),
    (L.ticket_id, " T-500069", ("T-500069", True)), (L.ticket_id, "T-ABCDE", (None, False)),
    (L.order_id, " O-202400203", ("O-202400203", True)), (L.order_id, "O-2024X0001", (None, False)),
    (L.cashier_id, "EMP049✓", ("EMP049", True)), (L.cashier_id, "EM070", ("EMP070", True)),
    (L.cashier_id, "EMP00?", (None, False)),
    (L.till_id, "CJ02", ("CAJ02", True)), (L.till_id, "CAJXX", (None, False)),
    (L.employee_id, " fsh0001 ", ("FSH0001", True)), (L.employee_id, "FSH-0001", ("FSH0001", True)),
])
def test_ids(fn, raw, expected):
    assert fn(raw) == expected


def test_mappings():
    assert L.mapped("Tarjeta (Débito)", L.PAYMENT_STORE) == ("Tarjeta", True)
    assert L.mapped("Contado", L.PAYMENT_STORE) == ("Efectivo", True)
    assert L.mapped("BAJA VOL.", L.EXIT_TYPE) == ("Voluntaria", True)
    assert L.mapped("N2", L.LEVEL) == ("Semi Senior", True)
    assert L.mapped("GOLD", L.TIER) == ("Oro", True)
    assert L.mapped("Algo raro", L.TIER) == ("Algo raro", False)
    assert L.title_category("textil hogar") == "Textil hogar"
    assert L.parse_flag("sí") is True and L.parse_flag("N") is False and L.parse_flag("quizá") is None
    assert L.parse_date("2019-05-03") == date(2019, 5, 3)
