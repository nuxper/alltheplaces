import re
from typing import Any, AsyncIterator, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# The store locator embeds every centre in a "var BLOCK_MAP = {...}" object; the
# metropolitan-France/Belgium list and the Swiss list live on separate pages.
START_URLS = {
    "FR": "https://www.elephantbleu.com/ma-station-de-lavage/",
    "CH": "https://www.elephantbleu.com/fr-ch/ma-station-de-lavage/",
}

ALWAYS_OPEN_RE = re.compile(r"(24\s*h?\s*/\s*24|24\s*h\s*24|non\s*stop)", re.IGNORECASE)
SEVEN_DAYS_RE = re.compile(r"(7\s*j(?:ours)?\s*/\s*7|7\s*/\s*7|tous les jours)", re.IGNORECASE)
# A plain "6h-22h ~ 7 jours / 7" style range, with no weekday names in sight.
SIMPLE_RANGE_RE = re.compile(r"^\D*?(\d{1,2})\s*h\s*(\d{2})?\s*[-~à]+\s*(\d{1,2})\s*h\s*(\d{2})?")
WEEKDAY_WORDS_RE = re.compile(r"lun|mar|mer|jeu|ven|sam|dim|ferm", re.IGNORECASE)


class ElephantBleuSpider(Spider):
    name = "elephant_bleu"
    item_attributes = {"brand": "Éléphant Bleu", "brand_wikidata": "Q3144358"}
    allowed_domains = ["elephantbleu.com"]

    async def start(self) -> AsyncIterator[Request]:
        for country, url in START_URLS.items():
            yield Request(url, cb_kwargs={"country": country})

    def parse(self, response: Response, country: str, **kwargs: Any) -> Iterable[Feature]:
        blob = response.text[response.text.index("var BLOCK_MAP = ") + len("var BLOCK_MAP = ") :]
        for marker in chompjs.parse_js_object(blob)["markers"]:
            popup = Selector(text=marker["popmap"])

            item = Feature()
            item["lat"] = marker["lat"]
            item["lon"] = marker["lng"]
            item["branch"] = popup.css("p.h3__lightb::text").get("").strip() or None

            website = popup.css("a.button::attr(href)").re_first(r"\S+centre-elephant-bleu\S+")
            item["website"] = website
            item["ref"] = website.rstrip("/").rsplit("/", 1)[-1]

            lines = [t.strip() for t in popup.css("div.mb-2 p::text").getall() if t.strip()]
            address = lines[0] if lines else ""
            self._parse_address(address, country, item)
            if len(lines) > 1:
                item["opening_hours"] = self._parse_hours(" ".join(lines[1:]))

            apply_category(Categories.CAR_WASH, item)
            yield item

    @staticmethod
    def _parse_address(address: str, country: str, item: Feature) -> None:
        if match := re.search(r"\bB-(\d{4})\b", address):
            item["country"] = "BE"
            item["postcode"] = match.group(1)
        elif country == "CH" and (match := re.search(r"\b(\d{4})\b(?=\s+\D+$)", address)):
            item["country"] = "CH"
            item["postcode"] = match.group(1)
        elif matches := list(re.finditer(r"\b(\d{5})\b", address)):
            match = matches[-1]
            item["country"] = "FR"
            item["postcode"] = match.group(1)
        else:
            item["street_address"] = address or None
            return

        item["street_address"] = address[: match.start()].strip(" ,-") or None
        item["city"] = address[match.end() :].strip(" ,-") or None

    @staticmethod
    def _parse_hours(text: str) -> OpeningHours | None:
        # The popup hours are franchise-written free text with times before day
        # names and several clauses per line ("5h-21h du lu-sa, 8h-21h le
        # dimanche, ..."); feeding that to a generic parser silently mangles it.
        # Only the two unambiguous shorthands are safe to read: an always-open
        # "24h/24 7j/7" and a single "6h-22h 7j/7" range with no weekday names.
        oh = OpeningHours()
        if ALWAYS_OPEN_RE.search(text) and SEVEN_DAYS_RE.search(text):
            oh.add_days_range(DAYS, "00:00", "24:00")
            return oh

        if not WEEKDAY_WORDS_RE.search(text) and SEVEN_DAYS_RE.search(text):
            if match := SIMPLE_RANGE_RE.match(text):
                start = f"{int(match.group(1)):02d}:{match.group(2) or '00'}"
                end = f"{int(match.group(3)):02d}:{match.group(4) or '00'}"
                oh.add_days_range(DAYS, start, end)
                return oh

        return None
