"""Service logic for Discord-user-level profile preferences."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from player_self_service.dal import user_profile_preference_dal

logger = logging.getLogger(__name__)

ProfileField = Literal["timezone", "country", "language"]


@dataclass(frozen=True, slots=True)
class ProfilePreferenceChoice:
    label: str
    value: str
    description: str = ""


TIMEZONE_CHOICES: tuple[ProfilePreferenceChoice, ...] = (
    ProfilePreferenceChoice("UTC", "UTC", "Coordinated Universal Time"),
    ProfilePreferenceChoice("United Kingdom", "Europe/London", "Europe/London"),
    ProfilePreferenceChoice(
        "Central Europe", "Europe/Berlin", "Germany, Italy, Netherlands, Poland"
    ),
    ProfilePreferenceChoice("France / Spain", "Europe/Paris", "Europe/Paris"),
    ProfilePreferenceChoice("Eastern Europe", "Europe/Kyiv", "Ukraine and nearby regions"),
    ProfilePreferenceChoice("Turkey", "Europe/Istanbul", "Europe/Istanbul"),
    ProfilePreferenceChoice("Dubai / Gulf", "Asia/Dubai", "Asia/Dubai"),
    ProfilePreferenceChoice("India", "Asia/Kolkata", "Asia/Kolkata"),
    ProfilePreferenceChoice("Thailand / Vietnam", "Asia/Bangkok", "Asia/Bangkok"),
    ProfilePreferenceChoice("Indonesia West", "Asia/Jakarta", "Asia/Jakarta"),
    ProfilePreferenceChoice("Philippines", "Asia/Manila", "Asia/Manila"),
    ProfilePreferenceChoice("Singapore / Malaysia", "Asia/Singapore", "Asia/Singapore"),
    ProfilePreferenceChoice("China", "Asia/Shanghai", "Asia/Shanghai"),
    ProfilePreferenceChoice("Japan", "Asia/Tokyo", "Asia/Tokyo"),
    ProfilePreferenceChoice("Australia East", "Australia/Sydney", "Australia/Sydney"),
    ProfilePreferenceChoice("New Zealand", "Pacific/Auckland", "Pacific/Auckland"),
    ProfilePreferenceChoice("US Eastern", "America/New_York", "America/New_York"),
    ProfilePreferenceChoice("US Central", "America/Chicago", "America/Chicago"),
    ProfilePreferenceChoice("US Mountain", "America/Denver", "America/Denver"),
    ProfilePreferenceChoice("US Pacific", "America/Los_Angeles", "America/Los_Angeles"),
    ProfilePreferenceChoice("Brazil", "America/Sao_Paulo", "America/Sao_Paulo"),
    ProfilePreferenceChoice("Mexico City", "America/Mexico_City", "America/Mexico_City"),
    ProfilePreferenceChoice("South Africa", "Africa/Johannesburg", "Africa/Johannesburg"),
    ProfilePreferenceChoice("Egypt", "Africa/Cairo", "Africa/Cairo"),
)

COUNTRY_CHOICES: tuple[ProfilePreferenceChoice, ...] = tuple(
    ProfilePreferenceChoice(label, code)
    for label, code in (
        ("United Kingdom (GB)", "GB"),
        ("United States (US)", "US"),
        ("Germany (DE)", "DE"),
        ("France (FR)", "FR"),
        ("Spain (ES)", "ES"),
        ("Italy (IT)", "IT"),
        ("Netherlands (NL)", "NL"),
        ("Poland (PL)", "PL"),
        ("Ukraine (UA)", "UA"),
        ("Romania (RO)", "RO"),
        ("Turkey (TR)", "TR"),
        ("Brazil (BR)", "BR"),
        ("Mexico (MX)", "MX"),
        ("Canada (CA)", "CA"),
        ("Australia (AU)", "AU"),
        ("New Zealand (NZ)", "NZ"),
        ("India (IN)", "IN"),
        ("Indonesia (ID)", "ID"),
        ("Philippines (PH)", "PH"),
        ("Singapore (SG)", "SG"),
        ("Malaysia (MY)", "MY"),
        ("Japan (JP)", "JP"),
        ("South Korea (KR)", "KR"),
        ("South Africa (ZA)", "ZA"),
    )
)

LANGUAGE_CHOICES: tuple[ProfilePreferenceChoice, ...] = tuple(
    ProfilePreferenceChoice(label, tag)
    for label, tag in (
        ("English", "en"),
        ("English (UK)", "en-GB"),
        ("English (US)", "en-US"),
        ("German / Deutsch", "de"),
        ("French / Francais", "fr"),
        ("Spanish / Espanol", "es"),
        ("Portuguese", "pt"),
        ("Portuguese (Brazil)", "pt-BR"),
        ("Italian", "it"),
        ("Dutch", "nl"),
        ("Polish", "pl"),
        ("Ukrainian", "uk"),
        ("Turkish", "tr"),
        ("Russian", "ru"),
        ("Arabic", "ar"),
        ("Hindi", "hi"),
        ("Indonesian", "id"),
        ("Malay", "ms"),
        ("Thai", "th"),
        ("Vietnamese", "vi"),
        ("Chinese", "zh"),
        ("Chinese (Simplified)", "zh-CN"),
        ("Chinese (Traditional)", "zh-TW"),
        ("Japanese", "ja"),
        ("Korean", "ko"),
    )
)

PROFILE_CHOICES: dict[ProfileField, tuple[ProfilePreferenceChoice, ...]] = {
    "timezone": TIMEZONE_CHOICES,
    "country": COUNTRY_CHOICES,
    "language": LANGUAGE_CHOICES,
}

COUNTRY_NAMES: dict[str, str] = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua & Barbuda",
    "AI": "Anguilla",
    "AL": "Albania",
    "AM": "Armenia",
    "AO": "Angola",
    "AR": "Argentina",
    "AS": "American Samoa",
    "AT": "Austria",
    "AU": "Australia",
    "AW": "Aruba",
    "AX": "Aland Islands",
    "AZ": "Azerbaijan",
    "BA": "Bosnia & Herzegovina",
    "BB": "Barbados",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BL": "St. Barthelemy",
    "BM": "Bermuda",
    "BN": "Brunei",
    "BO": "Bolivia",
    "BQ": "Bonaire, Sint Eustatius and Saba",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CA": "Canada",
    "CC": "Cocos (Keeling) Islands",
    "CD": "Congo (DRC)",
    "CF": "Central African Republic",
    "CG": "Congo",
    "CH": "Switzerland",
    "CI": "Cote d'Ivoire",
    "CK": "Cook Islands",
    "CL": "Chile",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CV": "Cabo Verde",
    "CW": "Curacao",
    "CX": "Christmas Island",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "ER": "Eritrea",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FK": "Falkland Islands",
    "FM": "Micronesia",
    "FO": "Faroe Islands",
    "FR": "France",
    "GA": "Gabon",
    "GB": "United Kingdom",
    "GD": "Grenada",
    "GE": "Georgia",
    "GF": "French Guiana",
    "GG": "Guernsey",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GL": "Greenland",
    "GM": "Gambia",
    "GN": "Guinea",
    "GP": "Guadeloupe",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GT": "Guatemala",
    "GU": "Guam",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HK": "Hong Kong SAR",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IM": "Isle of Man",
    "IN": "India",
    "IO": "British Indian Ocean Territory",
    "IQ": "Iraq",
    "IR": "Iran",
    "IS": "Iceland",
    "IT": "Italy",
    "JE": "Jersey",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "St. Kitts & Nevis",
    "KP": "North Korea",
    "KR": "South Korea",
    "KW": "Kuwait",
    "KY": "Cayman Islands",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LB": "Lebanon",
    "LC": "St. Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "LY": "Libya",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MF": "St. Martin",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MN": "Mongolia",
    "MO": "Macao SAR",
    "MP": "Northern Mariana Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MS": "Montserrat",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MX": "Mexico",
    "MY": "Malaysia",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NU": "Niue",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PA": "Panama",
    "PE": "Peru",
    "PF": "French Polynesia",
    "PG": "Papua New Guinea",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PM": "St. Pierre & Miquelon",
    "PN": "Pitcairn Islands",
    "PR": "Puerto Rico",
    "PS": "Palestinian Authority",
    "PT": "Portugal",
    "PW": "Palau",
    "PY": "Paraguay",
    "QA": "Qatar",
    "RE": "Reunion",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russia",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SE": "Sweden",
    "SG": "Singapore",
    "SH": "St Helena, Ascension, Tristan da Cunha",
    "SI": "Slovenia",
    "SJ": "Svalbard & Jan Mayen",
    "SK": "Slovakia",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SN": "Senegal",
    "SO": "Somalia",
    "SR": "Suriname",
    "SS": "South Sudan",
    "ST": "Sao Tome & Principe",
    "SV": "El Salvador",
    "SX": "Sint Maarten",
    "SY": "Syria",
    "SZ": "Eswatini",
    "TC": "Turks & Caicos Islands",
    "TD": "Chad",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TR": "Turkey",
    "TT": "Trinidad & Tobago",
    "TV": "Tuvalu",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UG": "Uganda",
    "UM": "U.S. Outlying Islands",
    "US": "United States",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VA": "Vatican City",
    "VC": "St. Vincent & Grenadines",
    "VE": "Venezuela",
    "VG": "British Virgin Islands",
    "VI": "U.S. Virgin Islands",
    "VN": "Vietnam",
    "VU": "Vanuatu",
    "WF": "Wallis & Futuna",
    "WS": "Samoa",
    "XK": "Kosovo",
    "YE": "Yemen",
    "YT": "Mayotte",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

COUNTRY_ALIASES: dict[str, str] = {
    "america": "US",
    "britain": "GB",
    "england": "GB",
    "great britain": "GB",
    "south korea": "KR",
    "uae": "AE",
    "uk": "GB",
    "united kingdom": "GB",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
}

LANGUAGE_NAMES: dict[str, str] = {
    "ar": "Arabic",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "hi": "Hindi",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "zh": "Chinese",
}

LANGUAGE_ALIASES: dict[str, str] = {
    "chinese simplified": "zh-CN",
    "chinese traditional": "zh-TW",
    "english": "en",
    "french": "fr",
    "german": "de",
    "indonesian": "id",
    "japanese": "ja",
    "korean": "ko",
    "mandarin": "zh-CN",
    "portuguese brazil": "pt-BR",
    "portuguese": "pt",
    "spanish": "es",
    "thai": "th",
    "vietnamese": "vi",
}


@dataclass(frozen=True, slots=True)
class UserProfilePreference:
    timezone_name: str | None = None
    location_country_code: str | None = None
    preferred_language_tag: str | None = None
    updated_at_utc: Any | None = None

    @property
    def timezone_label(self) -> str:
        return self.timezone_name or "not set"

    @property
    def country_label(self) -> str:
        if not self.location_country_code:
            return "not set"
        return country_display_name(self.location_country_code)

    @property
    def language_label(self) -> str:
        if not self.preferred_language_tag:
            return "not set"
        return language_display_name(self.preferred_language_tag)

    @property
    def summary_lines(self) -> tuple[str, str, str]:
        return (
            f"Timezone: {self.timezone_label}",
            f"Location: {self.country_label}",
            f"Language: {self.language_label}",
        )


@dataclass(frozen=True, slots=True)
class UserProfilePreferenceRead:
    ok: bool
    profile: UserProfilePreference = UserProfilePreference()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class UserProfilePreferenceMutationResult:
    ok: bool
    message: str
    profile: UserProfilePreference | None = None
    error: str | None = None


ProfileReader = Callable[[int], dict[str, Any] | None]
ProfileWriter = Callable[..., dict[str, Any]]


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_key(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def normalize_timezone(value: str | None) -> tuple[str | None, str | None]:
    raw = _clean(value)
    if not raw:
        return None, "Timezone is required. Use an IANA timezone like Europe/London."
    candidate = raw.replace(" ", "_")
    if len(candidate) > 64:
        return None, "Timezone is too long. Use an IANA timezone like Europe/London."
    try:
        ZoneInfo(candidate)
    except (ValueError, ZoneInfoNotFoundError):
        return (
            None,
            "Timezone must be an IANA timezone, for example Europe/London or America/New_York.",
        )
    return candidate, None


def normalize_country(value: str | None) -> tuple[str | None, str | None]:
    raw = _clean(value)
    if not raw:
        return (
            None,
            "Location country is required. Use a country name like United Kingdom or a code like GB.",
        )
    key = _normalize_key(raw)
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key], None

    code = raw.upper()
    if len(code) == 2 and code.isalpha():
        if code in COUNTRY_NAMES:
            return code, None
        return None, f"Country code `{code}` is not supported yet."

    for item_code, name in COUNTRY_NAMES.items():
        if _normalize_key(name) == key:
            return item_code, None
    return (
        None,
        "Location country was not recognised. Use a country name like United Kingdom or a code like GB.",
    )


def _canonical_language_tag(value: str) -> str:
    parts = [part for part in value.replace("_", "-").split("-") if part]
    if not parts:
        return ""
    primary = parts[0].lower()
    if not (2 <= len(primary) <= 8 and primary.isalpha()):
        return ""
    rest = []
    for part in parts[1:]:
        if not (1 <= len(part) <= 8 and part.isalnum()):
            return ""
        if len(part) == 2 and part.isalpha():
            rest.append(part.upper())
        elif len(part) == 4 and part.isalpha():
            rest.append(part.title())
        else:
            rest.append(part.lower())
    return "-".join((primary, *rest))


def normalize_language(value: str | None) -> tuple[str | None, str | None]:
    raw = _clean(value)
    if not raw:
        return (
            None,
            "Preferred language is required. Use a language name like English or a tag like en-GB.",
        )
    key = _normalize_key(raw)
    tag = LANGUAGE_ALIASES.get(key) or _canonical_language_tag(raw)
    if len(tag) > 35:
        return None, "Preferred language tag is too long. Use a tag like en-GB."
    primary = tag.split("-", 1)[0].lower()
    if primary in LANGUAGE_NAMES:
        return tag, None
    return (
        None,
        "Preferred language was not recognised. Use a language name like English or a tag like en-GB.",
    )


def country_display_name(code: str | None) -> str:
    normalized = _clean(code).upper()
    if not normalized:
        return "not set"
    name = COUNTRY_NAMES.get(normalized)
    return f"{name} ({normalized})" if name else normalized


def language_display_name(tag: str | None) -> str:
    normalized = _canonical_language_tag(_clean(tag))
    if not normalized:
        return "not set"
    primary = normalized.split("-", 1)[0].lower()
    name = LANGUAGE_NAMES.get(primary)
    return f"{name} ({normalized})" if name else normalized


def timezone_display_name(timezone_name: str | None) -> str:
    normalized, error = normalize_timezone(timezone_name)
    if error or normalized is None:
        return "Saved value unavailable" if _clean(timezone_name) else "Not set"
    known = next((choice.label for choice in TIMEZONE_CHOICES if choice.value == normalized), None)
    return known or normalized.replace("_", " ")


def profile_value_display(
    field: ProfileField,
    value: str | None,
) -> tuple[bool, bool, str, str | None]:
    """Return set/available/friendly-label/code without exposing unknown raw keys."""
    raw = _clean(value)
    if not raw:
        return False, True, "Not set", None
    if field == "timezone":
        normalized, error = normalize_timezone(raw)
        if error or normalized is None:
            return True, False, "Saved timezone unavailable", None
        return True, True, timezone_display_name(normalized), normalized
    if field == "country":
        normalized, error = normalize_country(raw)
        if error or normalized is None:
            return True, False, "Saved location unavailable", None
        return True, True, country_display_name(normalized), normalized
    if field == "language":
        normalized, error = normalize_language(raw)
        if error or normalized is None:
            return True, False, "Saved language unavailable", None
        return True, True, language_display_name(normalized), normalized
    raise ValueError(f"Unsupported profile preference field: {field}")


def _profile_from_row(row: dict[str, Any] | None) -> UserProfilePreference:
    if not row:
        return UserProfilePreference()
    return UserProfilePreference(
        timezone_name=_clean(row.get("TimezoneName")) or None,
        location_country_code=(_clean(row.get("LocationCountryCode")).upper() or None),
        preferred_language_tag=_clean(row.get("PreferredLanguageTag")) or None,
        updated_at_utc=row.get("UpdatedAtUtc"),
    )


async def read_user_profile_preference(
    discord_user_id: int,
    *,
    reader: ProfileReader = user_profile_preference_dal.fetch_profile_preference,
) -> UserProfilePreferenceRead:
    try:
        row = await asyncio.to_thread(reader, int(discord_user_id))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("profile_preference_read_failed user_id=%s", discord_user_id)
        return UserProfilePreferenceRead(ok=False, error=f"{type(exc).__name__}: {exc}")
    return UserProfilePreferenceRead(ok=True, profile=_profile_from_row(row))


async def _write_field(
    discord_user_id: int,
    field: ProfileField,
    value: str | None,
    *,
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference_field,
) -> UserProfilePreference:
    row = await asyncio.to_thread(
        writer,
        discord_user_id=int(discord_user_id),
        field=field,
        value=value,
        updated_by_discord_user_id=int(discord_user_id),
    )
    return _profile_from_row(row)


async def set_profile_preference(
    discord_user_id: int,
    field: ProfileField,
    value: str,
    *,
    reader: ProfileReader = user_profile_preference_dal.fetch_profile_preference,
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference_field,
) -> UserProfilePreferenceMutationResult:
    _ = reader  # Retained for compatibility; the atomic writer returns the authoritative row.
    if field == "timezone":
        normalized, error = normalize_timezone(value)
    elif field == "country":
        normalized, error = normalize_country(value)
    elif field == "language":
        normalized, error = normalize_language(value)
    else:
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preference field was not recognised.",
        )
    if error:
        return UserProfilePreferenceMutationResult(ok=False, message=error)
    try:
        updated = await _write_field(int(discord_user_id), field, normalized, writer=writer)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception(
            "profile_preference_set_failed user_id=%s field=%s",
            discord_user_id,
            field,
        )
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preference could not be saved. Your previous setting is unchanged.",
            error=f"{type(exc).__name__}: {exc}",
        )

    label = _field_value_label(field, updated)
    logger.info(
        "profile_preference_saved user_id=%s field=%s",
        discord_user_id,
        field,
    )
    return UserProfilePreferenceMutationResult(
        ok=True,
        message=f"{_field_label(field)} saved as {label}.",
        profile=updated,
    )


async def clear_profile_preference(
    discord_user_id: int,
    field: ProfileField,
    *,
    reader: ProfileReader = user_profile_preference_dal.fetch_profile_preference,
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference_field,
) -> UserProfilePreferenceMutationResult:
    _ = reader  # Retained for compatibility; no read-before-write is required for a field clear.
    if field not in PROFILE_CHOICES:
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preference field was not recognised.",
        )
    try:
        updated = await _write_field(int(discord_user_id), field, None, writer=writer)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception(
            "profile_preference_clear_failed user_id=%s field=%s",
            discord_user_id,
            field,
        )
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preference could not be removed. Your previous setting is unchanged.",
            error=f"{type(exc).__name__}: {exc}",
        )
    logger.info("profile_preference_removed user_id=%s field=%s", discord_user_id, field)
    return UserProfilePreferenceMutationResult(
        ok=True,
        message=f"{_field_label(field)} removed.",
        profile=updated,
    )


def _field_label(field: ProfileField) -> str:
    return {
        "timezone": "Timezone",
        "country": "Location country",
        "language": "Preferred language",
    }[field]


def _field_value_label(field: ProfileField, profile: UserProfilePreference) -> str:
    if field == "timezone":
        return profile.timezone_label
    if field == "country":
        return profile.country_label
    return profile.language_label
