import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FeuVertFRSpider(SitemapSpider, StructuredDataSpider):
    name = "feu_vert_fr"
    item_attributes = {"brand": "Feu Vert", "brand_wikidata": "Q3070922"}
    sitemap_urls = ["https://www.feuvert.fr/sitemap/centres-auto.xml"]
    # The sitemap also lists department (/centres-auto/<dept>/<code>.html) and city
    # (/centres-auto/<city>.html) listing pages; only the three-segment URLs are centres.
    sitemap_rules = [(r"/centres-auto/[^/]+/[^/]+/(\d+)\.html$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    requires_proxy = "FR"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # Opening hours are published under the non-standard "hoursAvailable" key, with
        # each dayOfWeek given as a {"name": "monday", ...} object rather than a string.
        if hours := ld_data.pop("hoursAvailable", None):
            for spec in hours:
                if isinstance(spec.get("dayOfWeek"), list):
                    spec["dayOfWeek"] = [day.get("name") if isinstance(day, dict) else day for day in spec["dayOfWeek"]]
            ld_data["openingHoursSpecification"] = hours

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("/", 1)[-1].removesuffix(".html")

        branch = re.sub(r"^FEU\s*VERT\s+", "", item.pop("name", "") or "", flags=re.IGNORECASE)
        item["branch"] = " ".join(branch.split()) or None

        # Coordinates sit on non-standard top-level properties rather than "geo".
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")

        # Every centre carries the same stock illustration rather than a storefront photo.
        item.pop("image", None)

        # The postcode is absent from the JSON-LD address but appears in the rendered
        # "Adresse" block, formatted as "<street> <postcode> <city>".
        if not item.get("postcode"):
            address = response.xpath(
                '//p[contains(@class, "title") and normalize-space()="Adresse"]'
                '/following-sibling::p[contains(@class, "text")][1]/text()'
            ).get("")
            if m := re.search(r"\b(\d{5})\b", address):
                item["postcode"] = m.group(1)

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
