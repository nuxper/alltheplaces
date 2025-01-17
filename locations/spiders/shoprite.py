# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.hours import OpeningHours, day_range, DAYS
from locations.items import GeojsonPointItem

kDaysRe = re.compile(f"(?:({'|'.join(DAYS)})\w*)")
kTimesRe = re.compile(r"(\d+)(:\d+)? *([APap][Mm])")


class ShopriteSpider(scrapy.Spider):
    name = "shoprite"
    item_attributes = {"brand": "ShopRite", "brand_wikidata": "Q7501097"}
    allowed_domains = ["shoprite.com"]
    start_urls = [
        "https://www.shoprite.com/",
    ]

    def parse(self, response):
        script = response.xpath(
            '//script[contains(text(), "__PRELOADED_STATE__")]/text()'
        ).extract_first()
        script = script[script.index("{") :]
        stores = json.loads(script)["stores"]["availablePlanningStores"]["items"]

        for store in stores:
            ref = store["retailerStoreId"]
            properties = {
                "ref": ref,
                "website": f"https://www.shoprite.com/sm/planning/rsid/{ref}",
                "name": store["name"],
                "lat": store["location"]["latitude"],
                "lon": store["location"]["longitude"],
                "street_address": store["addressLine1"],
                "city": store["city"],
                "state": store["countyProvinceState"],
                "postcode": store["postCode"],
                "country": store["country"],
                "phone": store["phone"],
                "opening_hours": self.parse_hours(store["openingHours"]),
            }

            yield GeojsonPointItem(**properties)

    @staticmethod
    def parse_hours(hours):
        if hours is None:
            return
        oh = OpeningHours()
        for row in re.split(r" *[\n|,] *", hours):
            row = row.strip()
            if row == "":
                continue
            if " daily" in row:
                row = "Mo-Sa " + row.replace(" daily", "")
            row = re.sub("open 24 hours", "12 am - 12 am", row, flags=re.I)
            start_time, end_time = map(list, kTimesRe.findall(row))
            start_time[1] = start_time[1] or ":00"
            end_time[1] = end_time[1] or ":00"
            start_time = "".join(start_time)
            end_time = "".join(end_time)
            days = kDaysRe.findall(row)
            if len(days) == 2:
                for day in day_range(*days):
                    oh.add_range(day, start_time, end_time, "%I:%M%p")
            else:
                oh.add_range(days[0], start_time, end_time, "%I:%M%p")
            return oh.as_opening_hours()
