# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AldiUSSpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_us"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q125054"}
    allowed_domains = ["stores.aldi.us"]
    sitemap_urls = ["https://stores.aldi.us/robots.txt"]
    sitemap_rules = [
        (r"^https://stores\.aldi\.us/.*/.*/.*$", "parse"),
    ]
    wanted_types = ["GroceryStore"]

    def parse(self, response):
        for city in response.css('[itemprop="address"] .Address-city'):
            city.root.set("itemprop", "addressLocality")
        yield from self.parse_sd(response)
