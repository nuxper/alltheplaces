import time

import pytest

from locations.hours import (
    CLOSED_FR,
    CLOSED_IT,
    DAYS,
    DAYS_BG,
    DAYS_DE,
    DAYS_ES,
    DAYS_FR,
    DAYS_IT,
    DAYS_PL,
    DAYS_RU,
    DELIMITERS_ES,
    DELIMITERS_FR,
    DELIMITERS_IT,
    DELIMITERS_RU,
    NAMED_DAY_RANGES_IT,
    NAMED_DAY_RANGES_RU,
    NAMED_TIMES_IT,
    NAMED_TIMES_RU,
    OpeningHours,
    day_range,
    sanitise_day,
)


def test_day_range():
    for day in DAYS:
        assert day_range(day, day) == [day]
    for day, next_day in zip(DAYS, DAYS[1:] + DAYS[:1]):
        assert sorted(day_range(next_day, day), key=DAYS.index) == DAYS


def test_duplicates():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Mo", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo 07:00-17:00"


def test_times():
    o = OpeningHours()
    o.add_range("Mo", time.strptime("07:00", "%H:%M"), time.strptime("17:00", "%H:%M"))
    o.add_range("Tu", "09:00", "19:00")
    # Invalid ranges which should be ignored (single times, not ranges).
    o.add_range("We", "00:00", "00:00")
    o.add_range("Th", "15:55", "15:55")

    assert o.as_opening_hours() == "Mo 07:00-17:00; Tu 09:00-19:00"


def test_two_ranges():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Tu", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")

    o.add_range("Fr", "08:00", "17:00")
    o.add_range("Sa", "08:00", "17:00")

    assert o.as_opening_hours() == "Mo-We 07:00-17:00; Fr-Sa 08:00-17:00"


def test_mixed_ranges():
    o = OpeningHours()
    o.add_range("Mo", "08:00", "17:00")
    o.add_range("Tu", "08:00", "17:00")
    o.add_range("We", "09:00", "18:00")
    o.add_range("Th", "09:00", "18:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Su", "09:00", "17:00")

    assert o.as_opening_hours() == "Mo-Tu 08:00-17:00; We-Th 09:00-18:00; Fr 07:00-17:00; Su 09:00-17:00"


def test_closed_sunday():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("Tu", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")
    o.add_range("Th", "07:00", "17:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Sa", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo-Sa 07:00-17:00"


def test_closed_tuesday():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "17:00")
    o.add_range("We", "07:00", "17:00")
    o.add_range("Th", "07:00", "17:00")
    o.add_range("Fr", "07:00", "17:00")
    o.add_range("Sa", "07:00", "17:00")
    o.add_range("Su", "07:00", "17:00")

    assert o.as_opening_hours() == "Mo 07:00-17:00; We-Su 07:00-17:00"


def test_twentyfour_seven():
    o = OpeningHours()
    o.add_range("Mo", "0:00", "23:59")
    o.add_range("Tu", "0:00", "23:59")
    o.add_range("We", "0:00", "23:59")
    o.add_range("Th", "0:00", "23:59")
    o.add_range("Fr", "0:00", "23:59")
    o.add_range("Sa", "0:00", "23:59")
    o.add_range("Su", "0:00", "23:59")

    assert o.as_opening_hours() == "Mo-Su 00:00-24:00"


def test_no_opening_hours():
    o = OpeningHours()
    assert o.as_opening_hours() == ""


def test_multiple_times():
    o = OpeningHours()
    o.add_range("Mo", "08:00", "12:00")
    o.add_range("Mo", "13:00", "17:30")
    assert o.as_opening_hours() == "Mo 08:00-12:00,13:00-17:30"

    o2 = OpeningHours()
    o2.add_range("Tu", "09:00", "12:00")
    o2.add_range("Tu", "15:00", "17:00")
    assert o2.as_opening_hours() == "Tu 09:00-12:00,15:00-17:00"

    o3 = OpeningHours()
    o3.add_range("Tu", "15:00", "17:00")
    o3.add_range("Tu", "09:00", "12:00")
    assert o3.as_opening_hours() == "Tu 09:00-12:00,15:00-17:00"


def test_simple_over_midnight():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "02:00")
    assert o.as_opening_hours() == "Mo 07:00-24:00; Tu 00:00-02:00"


def test_hours_over_midnight_overide_closed_days_on_next_day():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "02:00")
    o.set_closed("Tu")
    assert o.as_opening_hours() == "Mo 07:00-24:00; Tu 00:00-02:00"


def test_hours_over_midnight_removed_when_start_day_set_to_closed():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "02:00")
    o.set_closed("Mo")
    assert o.as_opening_hours() == "Mo closed"


def test_over_midnight():
    o = OpeningHours()
    o.add_range("Mo", "07:00", "02:00")
    o.add_range("Tu", "07:00", "02:00")
    o.add_range("We", "07:00", "02:00")
    o.add_range("Th", "07:00", "02:00")
    o.add_range("Fr", "07:00", "02:00")
    o.add_range("Sa", "07:00", "02:00")
    o.add_range("Su", "05:00", "03:00")

    assert (
        o.as_opening_hours() == "Mo 00:00-03:00,07:00-24:00; Tu-Sa 00:00-02:00,07:00-24:00; Su 00:00-02:00,05:00-24:00"
    )


def test_till_midnight():
    o = OpeningHours()
    o.add_range("Mo", "11:00", "23:00")
    o.add_range("Tu", "11:00", "23:00")
    o.add_range("We", "11:00", "23:00")
    o.add_range("Th", "11:00", "23:00")
    o.add_range("Fr", "11:00", "24:00")
    o.add_range("Sa", "11:00", "24:00")
    o.add_range("Su", "11:00", "23:00")

    assert o.as_opening_hours() == "Mo-Th 11:00-23:00; Fr-Sa 11:00-24:00; Su 11:00-23:00"


def test_till_midnight_formatted_as_zero_hour():
    o = OpeningHours()
    o.add_range("Mo", "11:00", "0:00")

    assert o.as_opening_hours() == "Mo 11:00-24:00"


def test_till_midnight_formatted_as_twenty_four_hour():
    o = OpeningHours()
    o.add_range("Mo", "11:00", "24:00")

    assert o.as_opening_hours() == "Mo 11:00-24:00"


def test_till_midnight_formatted_in_other_unusual_formats():
    o = OpeningHours()
    o.add_range("Mo", "11:00:00", "00:00:00", time_format="%H:%M:%S")

    assert o.as_opening_hours() == "Mo 11:00-24:00"

    o = OpeningHours()
    o.add_range("Mo", "11:00:00", "0:00:00", time_format="%H:%M:%S")

    assert o.as_opening_hours() == "Mo 11:00-24:00"

    o = OpeningHours()
    o.add_range("Mo", "11:00:00", "24:00:00", time_format="%H:%M:%S")

    assert o.as_opening_hours() == "Mo 11:00-24:00"


def test_sanitise_days():
    assert sanitise_day("Mo") == "Mo"
    assert sanitise_day("Mon") == "Mo"
    assert sanitise_day("MONDAY") == "Mo"
    assert sanitise_day("schema.org/monday") == "Mo"
    assert sanitise_day("https://schema.org/monday") == "Mo"
    assert sanitise_day("http://schema.org/monday") == "Mo"
    assert sanitise_day("http://purl.org/goodrelations/v1#Monday") == "Mo"
    assert sanitise_day("   Monday ") == "Mo"
    assert sanitise_day("not_a_day") is None
    assert sanitise_day("пон", DAYS_BG) == "Mo"
    assert sanitise_day("Съб. ", DAYS_BG) == "Sa"
    assert sanitise_day("Съб. ", DAYS_DE) is None
    assert sanitise_day("Mo", DAYS_DE) == "Mo"
    assert sanitise_day("Do", DAYS_DE) == "Th"


def test_opening_hours_closed():
    oh = OpeningHours()
    oh.set_closed("Su")
    assert oh.as_opening_hours() == "Su closed"
    oh.set_closed(DAYS)
    assert oh.as_opening_hours() == "Mo-Su closed"


def test_add_ranges_from_string():
    o = OpeningHours()
    o.add_ranges_from_string("Monday-Wednesday: 5pm - 7pm")
    o.add_ranges_from_string("Monday-Wednesday 08:00-14:00")
    o.add_ranges_from_string("Monday to Tuesday: 15:00:01 to 16:35")
    o.add_ranges_from_string("Thurs 2PM-6:30P.M.")
    o.add_ranges_from_string(" Fri    9 a.m.  -  11am ")
    o.add_ranges_from_string("Weekends: 8:00 AM to 6:00 PM")
    assert (
        o.as_opening_hours()
        == "Mo-Tu 08:00-14:00,15:00-16:35,17:00-19:00; We 08:00-14:00,17:00-19:00; Th 14:00-18:30; Fr 09:00-11:00; Sa-Su 08:00-18:00"
    )

    o = OpeningHours()
    o.add_ranges_from_string("Monday to Thursday 7am to 7pm, Friday 12am to 11:59pm, Weekends CLOSED")
    assert o.as_opening_hours() == "Mo-Th 07:00-19:00; Fr 00:00-24:00; Sa-Su closed"

    o = OpeningHours()
    o.add_ranges_from_string("Monday to Tuesday 0:45 AM to 11:45 PM")
    assert o.as_opening_hours() == "Mo-Tu 00:45-23:45"

    o = OpeningHours()
    o.add_ranges_from_string("Sunday to Thursday 0800-1400, Wed-Sat 1300-1800")
    assert o.as_opening_hours() == "Mo-Tu 08:00-14:00; We-Th 08:00-14:00,13:00-18:00; Fr-Sa 13:00-18:00; Su 08:00-14:00"

    o = OpeningHours()
    o.add_ranges_from_string("Monday - Sunday: 00:00 - 23:59")
    assert o.as_opening_hours() == "Mo-Su 00:00-24:00"

    o = OpeningHours()
    o.add_ranges_from_string("Monday: 08:00 - Midday, 14:00 - Midnight   tue-sat: Midnight-0800")
    assert o.as_opening_hours() == "Mo 08:00-12:00,14:00-24:00; Tu-Sa 00:00-08:00"

    o = OpeningHours()
    o.add_ranges_from_string("Wed 2am-3am, 11am-1pm, 6pm-7pm, Thu midday-3:30pm 4:30pm-5:15pm")
    assert o.as_opening_hours() == "We 02:00-03:00,11:00-13:00,18:00-19:00; Th 12:00-15:30,16:30-17:15"

    o = OpeningHours()
    o.add_ranges_from_string(
        "MON-THU: 8:00 - 8:00 PM FRI: 8:00 AM - 10:00 PM SAT: 9:00 AM - 10:00 PM SUN: 9:00 AM - 8:00 PM"
    )
    assert o.as_opening_hours() == "Mo-Th 08:00-20:00; Fr 08:00-22:00; Sa 09:00-22:00; Su 09:00-20:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "Lunes a Domingo: 11:00 a 20:30 / Viernes y Sábado: 11:00 a 21:00",
        days=DAYS_ES,
        named_day_ranges={},
        delimiters=DELIMITERS_ES,
    )
    o.add_ranges_from_string(
        "Lunes a Sábado de 09:00 a 10:15 / Domingo de 09:00:00 a 10:00:00",
        days=DAYS_ES,
        named_day_ranges={},
        delimiters=DELIMITERS_ES,
    )
    assert (
        o.as_opening_hours()
        == "Mo-Th 09:00-10:15,11:00-20:30; Fr-Sa 09:00-10:15,11:00-20:30,11:00-21:00; Su 09:00-10:00,11:00-20:30"
    )

    o = OpeningHours()
    o.add_ranges_from_string(
        "{Sun|056:00AM-08:00PM}{Mon|05:00AM-09:00PM}{Tue|05:00AM-09:00PM}{Wed|05:00AM-09:00PM}{Thu|05:00AM-09:00PM}{Fri|05:00AM-09:00PM}{Sat|c}"
    )
    assert o.as_opening_hours() == "Mo-Fr 05:00-21:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "{Sun|056:00AM-08:00PM}{Mon|05:00AM-09:00PM}{Tue|05:00AM-09:00PM}{Wed|05:00AM-09:00PM}{Thu|05:00AM-09:00PM}{Fri|05:00AM-09:00PM}{Sat|c}",
        closed=["c"],
    )
    assert o.as_opening_hours() == "Mo-Fr 05:00-21:00; Sa closed"

    o = OpeningHours()
    o.add_ranges_from_string("Mo-Tu 06-12,We 14-18:30,Th 09-17,Fr 04-24,Sa-Su 00:00-11:59")
    assert (
        o.as_opening_hours() == "Mo-Tu 06:00-12:00; We 14:00-18:30; Th 09:00-17:00; Fr 04:00-24:00; Sa-Su 00:00-11:59"
    )

    o = OpeningHours()
    o.add_ranges_from_string(
        "[по будням: 10:00 - 21:00], [в субботу: 10:00 - 20:00], [в воскресенье: 10:00 - 21:00]",
        DAYS_RU,
        NAMED_DAY_RANGES_RU,
        NAMED_TIMES_RU,
        DELIMITERS_RU,
    )
    assert o.as_opening_hours() == "Mo-Fr 10:00-21:00; Sa 10:00-20:00; Su 10:00-21:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "pon.-sob. 10:00-18:00",
        DAYS_PL,
    )
    assert o.as_opening_hours() == "Mo-Sa 10:00-18:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "pn - pt 11:00 - 19:00",
        DAYS_PL,
    )
    assert o.as_opening_hours() == "Mo-Fr 11:00-19:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "pon-pt 08:00-19:00<br>sob 09:00-15:00",
        DAYS_PL,
    )
    assert o.as_opening_hours() == "Mo-Fr 08:00-19:00; Sa 09:00-15:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "lun 08:00-13:00;giorni feriali dalle 14:00 fino alle 18:00; prefestivi 12:00-16:00; domenica chiusi",
        DAYS_IT,
        NAMED_DAY_RANGES_IT,
        NAMED_TIMES_IT,
        DELIMITERS_IT,
        CLOSED_IT,
    )
    assert o.as_opening_hours() == "Mo 08:00-13:00,14:00-18:00; Tu-Fr 14:00-18:00; Sa 12:00-16:00; Su closed"

    o = OpeningHours()
    o.add_ranges_from_string(
        "tutti i giorni 08:00-13:00; feriali 15-18",
        DAYS_IT,
        NAMED_DAY_RANGES_IT,
        NAMED_TIMES_IT,
        DELIMITERS_IT,
        CLOSED_IT,
    )
    assert o.as_opening_hours() == "Mo-Fr 08:00-13:00,15:00-18:00; Sa-Su 08:00-13:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "all days 08:00-13:00; WEEKDAYS 15-18; friday closed",
    )
    assert o.as_opening_hours() == "Mo-Th 08:00-13:00,15:00-18:00; Fr closed; Sa-Su 08:00-13:00"

    o = OpeningHours()
    o.add_ranges_from_string(
        "Orario settimanale: lun - ven 9:00 - 13:00 / 15:00 - 19:30\nOrario continuato: sab 09:00 - 19:30Orario domenicale: 10:00 - 13:00 / 15:00 - 19:30",
        DAYS_IT,
        NAMED_DAY_RANGES_IT,
        NAMED_TIMES_IT,
        DELIMITERS_IT,
        CLOSED_IT,
    )
    assert o.as_opening_hours() == "Mo-Fr 09:00-13:00,15:00-19:30; Sa 09:00-19:30; Su 10:00-13:00,15:00-19:30"


# Real French opening-hours strings collected from spiders that each grew their own
# opening-hours regex (elephant_bleu, kookai_fr, mma_fr, les_cherubins_fr,
# la_taverne_table_de_caractere_fr). They are recorded here as the spec for
# improving the shared French handling in locations.hours, so spiders never need
# their own parsers. Each tuple is (source string, expected as_opening_hours(), id).

# Strings the shared French handling already parses correctly - regression guards
# for the core work.
FRENCH_HOURS_SUPPORTED = [
    ("Le samedi : 10 à 20h", "Sa 10:00-20:00", "kookai-bare-hour-before-a"),
    ("Lundi : 07:30 - 18:30", "Mo 07:30-18:30", "cherubins-single-day"),
    ("Dimanche : fermé", "Su closed", "kookai-closed-day"),
]

# Strings the shared French handling does NOT parse yet: each returns "" (no
# ranges), a wrong result, or raises. The xfail markers are strict - when a case
# starts parsing correctly, drop its marker in the same change.
FRENCH_HOURS_CASES = [
    # -- elephant_bleu (car-wash popups) --
    # "always open" idioms: 24h/24 + 7j/7 / "non stop" -> Mo-Su 00:00-24:00
    ("24h/24 7j/7", "Mo-Su 00:00-24:00", "always-24h-7j"),
    ("24h / 24 ~ 7 jours / 7", "Mo-Su 00:00-24:00", "always-spaced-tilde"),
    ("24/24 7/7", "Mo-Su 00:00-24:00", "always-bare"),
    ("non stop", "Mo-Su 00:00-24:00", "always-non-stop"),
    ("centre ouvert 7J/7 et 24H/24", "Mo-Su 00:00-24:00", "always-prose"),
    ("24h / 24 - 7 jours / 7", "Mo-Su 00:00-24:00", "always-dash-raises-indexerror"),
    # "7j/7" / "7 jours sur 7" as an all-week range around one time span
    ("6h-22h ~ 7 jours / 7", "Mo-Su 06:00-22:00", "allweek-range-tilde"),
    ("07h00-22h00 / 7 Jours sur 7", "Mo-Su 07:00-22:00", "allweek-range-slash"),
    ("6h30-23h00 7J/7", "Mo-Su 06:30-23:00", "allweek-range-halfhour"),
    ("7 jours sur 7 - 7 H-22H", "Mo-Su 07:00-22:00", "allweek-prose-raises-indexerror"),
    # "tous les jours" as a named all-week range
    ("Tous les jours de 7h à 21h", "Mo-Su 07:00-21:00", "tlj-de-a"),
    ("de 6h à 22h30 tous les jours", "Mo-Su 06:00-22:30", "tlj-trailing"),
    ("6h-22h tous les jours y compris les jours fériés", "Mo-Su 06:00-22:00", "tlj-range-prefix"),
    # time span stated BEFORE the day range ("5h-21h du lu-sa, ...")
    (
        "7h-20h du lu-sa, 8h-18h dimanche et jours fériés",
        "Mo-Sa 07:00-20:00; Su 08:00-18:00",
        "range-first-lu-sa-plus-su",
    ),
    (
        "5h-21h du lu-sa, 8h-21h le dimanche, fermé les jours fériés",
        "Mo-Sa 05:00-21:00; Su 08:00-21:00",
        "range-first-three-clauses",
    ),
    (
        "7h-21h du lu-ve, 8h-19h sa, 12h-16h dimanche et jours fériés",
        "Mo-Fr 07:00-21:00; Sa 08:00-19:00; Su 12:00-16:00",
        "range-first-lu-ve-sa-su",
    ),
    # time span before day range, with an explicit "fermé <jour>" clause
    (
        "7h-22h du lu-sa, fermé dimanche et jours fériés",
        "Mo-Sa 07:00-22:00; Su closed",
        "range-first-ferme-sunday",
    ),
    ("07H00 - 20H00 fermée le dimanche", "Mo-Sa 07:00-20:00; Su closed", "range-only-ferme-sunday"),
    # day range then "de Xh à Yh", bare "a" for "à", several day groups
    (
        "du lundi au samedi de 8h a 20 h dimanche de 9h a 12h",
        "Mo-Sa 08:00-20:00; Su 09:00-12:00",
        "de-a-two-groups",
    ),
    (
        "8h30 à 19h du lundi au samedi, 8h30-12h30 dimanches et jours fériés",
        "Mo-Sa 08:30-19:00; Su 08:30-12:30",
        "range-first-then-du-lundi",
    ),
    # bare time span, no day mentioned -> assume the whole week
    ("7h-20h", "Mo-Su 07:00-20:00", "bare-range-dash"),
    ("07h00 / 22h00", "Mo-Su 07:00-22:00", "bare-range-slash"),
    # explicit French day range, only the "9h30" time notation blocks it
    ("Du lundi au dimanche de 07h00 - 21h00", "Mo-Su 07:00-21:00", "h-notation-lundi-dimanche"),
    (
        "Lu - Sa 07h00 - 20h00 / Dimanche et jours fériés 09h00 - 19h00",
        "Mo-Sa 07:00-20:00; Su 09:00-19:00",
        "h-notation-lu-sa-plus-dimanche",
    ),
    # -- kookai_fr (free-text rows) --
    ("Du lundi au vendredi : 9h30 - 19h", "Mo-Fr 09:30-19:00", "kookai-h-notation-range"),
    ("Lundi : 13h 14h 18h 19h", "Mo 13:00-14:00,18:00-19:00", "kookai-bare-hours-two-ranges"),
    # -- mma_fr (per-day dict, spaced "HH h MM" slots) --
    ("Lundi 08 h 00 - 12 h 00", "Mo 08:00-12:00", "mma-spaced-h"),
    (
        "Lundi 08 h 30 - 12 h 00 Lundi 14 h 00 - 18 h 00",
        "Mo 08:30-12:00,14:00-18:00",
        "mma-spaced-h-two-slots",
    ),
    # -- les_cherubins_fr (per-day rows, "et" day connector) --
    ("Samedi et Dimanche : Fermé", "Sa-Su closed", "cherubins-et-connector-closed"),
    # -- la_taverne_table_de_caractere_fr (Elementor widgets, "HHhMM" slots) --
    ("Lundi 11h00 - 15h00 15h00 - 22h00", "Mo 11:00-15:00,15:00-22:00", "taverne-h-two-ranges"),
    ("Lundi 12h00 - 15h00 15h00 - 00h00", "Mo 12:00-15:00,15:00-24:00", "taverne-h-midnight-close"),
    ("Lundi 12h00 23h00", "Mo 12:00-23:00", "taverne-bare-pair-no-delimiter"),
]


@pytest.mark.parametrize(
    "source,expected",
    [pytest.param(source, expected, id=test_id) for source, expected, test_id in FRENCH_HOURS_SUPPORTED]
    + [
        pytest.param(
            source,
            expected,
            id=test_id,
            marks=pytest.mark.xfail(strict=True, reason="shared French opening-hours handling not implemented yet"),
        )
        for source, expected, test_id in FRENCH_HOURS_CASES
    ],
)
def test_add_ranges_from_string_french(source, expected):
    o = OpeningHours()
    o.add_ranges_from_string(
        source,
        days=DAYS_FR,
        named_day_ranges={},  # TODO: pass NAMED_DAY_RANGES_FR once it exists ("tous les jours", "7j/7", ...)
        delimiters=DELIMITERS_FR,
        closed=CLOSED_FR,
    )
    assert o.as_opening_hours() == expected


def test_oh_as_bool():
    # https://github.com/alltheplaces/alltheplaces/pull/8779#issue-2395034394
    o = OpeningHours()
    assert not o

    o = OpeningHours()
    o.add_range("Mo", "09:00", "17:00")
    assert o

    o = OpeningHours()
    o.set_closed("Mo")
    assert o
