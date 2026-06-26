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
ProfileWriter = Callable[..., None]


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
    except ZoneInfoNotFoundError:
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


def _profile_from_row(row: dict[str, Any] | None) -> UserProfilePreference:
    if not row:
        return UserProfilePreference()
    return UserProfilePreference(
        timezone_name=_clean(row.get("TimezoneName")) or None,
        location_country_code=(_clean(row.get("LocationCountryCode")).upper() or None),
        preferred_language_tag=(
            _canonical_language_tag(_clean(row.get("PreferredLanguageTag"))) or None
        ),
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


async def _write_profile(
    discord_user_id: int,
    profile: UserProfilePreference,
    *,
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference,
) -> None:
    await asyncio.to_thread(
        writer,
        discord_user_id=int(discord_user_id),
        timezone_name=profile.timezone_name,
        location_country_code=profile.location_country_code,
        preferred_language_tag=profile.preferred_language_tag,
        updated_by_discord_user_id=int(discord_user_id),
    )


async def set_profile_preference(
    discord_user_id: int,
    field: ProfileField,
    value: str,
    *,
    reader: ProfileReader = user_profile_preference_dal.fetch_profile_preference,
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference,
) -> UserProfilePreferenceMutationResult:
    current = await read_user_profile_preference(int(discord_user_id), reader=reader)
    if not current.ok:
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preferences are temporarily unavailable. Please try again in a moment.",
            error=current.error,
        )

    timezone_name = current.profile.timezone_name
    country_code = current.profile.location_country_code
    language_tag = current.profile.preferred_language_tag
    if field == "timezone":
        timezone_name, error = normalize_timezone(value)
    elif field == "country":
        country_code, error = normalize_country(value)
    else:
        language_tag, error = normalize_language(value)
    if error:
        return UserProfilePreferenceMutationResult(ok=False, message=error)

    updated = UserProfilePreference(
        timezone_name=timezone_name,
        location_country_code=country_code,
        preferred_language_tag=language_tag,
    )
    try:
        await _write_profile(int(discord_user_id), updated, writer=writer)
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
    writer: ProfileWriter = user_profile_preference_dal.upsert_profile_preference,
) -> UserProfilePreferenceMutationResult:
    current = await read_user_profile_preference(int(discord_user_id), reader=reader)
    if not current.ok:
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Profile preferences are temporarily unavailable. Please try again in a moment.",
            error=current.error,
        )
    updated = UserProfilePreference(
        timezone_name=None if field == "timezone" else current.profile.timezone_name,
        location_country_code=None if field == "country" else current.profile.location_country_code,
        preferred_language_tag=(
            None if field == "language" else current.profile.preferred_language_tag
        ),
    )
    try:
        await _write_profile(int(discord_user_id), updated, writer=writer)
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
