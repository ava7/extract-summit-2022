import json
import urllib.parse

import scrapy
from scrapy.loader import ItemLoader

from spider.items import SpiderItem


def url_add_query_attr(url, query_attributes={}):
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(query)

    for attribute in query_attributes:
        query[attribute] = query_attributes[attribute]

    query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunsplit(("https", netloc, path, query, fragment))


class ExtractSummitSpider(scrapy.Spider):
    name = 'extract_summit'
    allowed_domains = ['extract-summit-kokb7ng7-5umjfyjn4a-ew.a.run.app']
    start_urls = ['https://extract-summit-kokb7ng7-5umjfyjn4a-ew.a.run.app/']
    custom_settings = {
        "ROBOTSTXT_OBEY": "true"
    }

    def parse(self, response):
        url = response.urljoin(response.css("li:nth-child(2) .external::attr(href)").get())
        return response.follow(url_add_query_attr(url, {"sort_by": "alphabetically"}),
                               callback=self.parse_category)

    def parse_category(self, response):
        for url in response.css('a[href*="item"]::attr(href)'):
            yield response.follow(url, callback=self.parse_item)

        link = response.css('.row[align="center"] a:last-child::attr(href)').get()
        yield response.follow(url_add_query_attr(link, {"sort_by": "alphabetically"}),
                              callback=self.parse_category)

    def parse_item(self, response):
        if team_items := response.css('a[href*="item"]::attr(href)').getall():
            for url in team_items:
                yield response.follow(url, callback=self.parse_item)

        loader = ItemLoader(item=SpiderItem(), selector=response)

        data = {}
        if response.css("#item-data-json::text"):
            data = json.loads(response.css("#item-data-json::text").get())

        loader.add_value("item_id", data.get("item_id"))
        loader.add_css("item_id", "#uuid::text")

        loader.add_value("name", data.get("name"))
        loader.add_css("name", "h2::text")

        loader.add_value("image_id", data.get("image_path"))
        loader.add_css("image_id", ".img-shadow img::attr(src)")
        loader.add_css("image_id", 'script:contains("i.src")::text', re="i.src = '(.+)?'")

        loader.add_css("phone", 'script:contains("cyphered_phone")::text', re=r'from\(\"(.+)?\"')

        if rating_url := response.css(".price::attr(data-price-url)").get():
            yield response.follow(rating_url,
                                  callback=self.extract_stock,
                                  meta={"item": loader.load_item()})
            return
        if rating_url := data.get("data_url"):
            yield response.follow(rating_url,
                                  callback=self.extract_stock,
                                  meta={"item": loader.load_item()})
            return

        loader.add_value("rating", data.get("rating"))
        loader.add_xpath("rating", "//*[contains(text(),'Rating')]/span/text()")
        loader.add_css("rating", ".price::text")

        yield loader.load_item()

    def extract_stock(self, response):
        data = json.loads(response.text)
        loader = ItemLoader(item=SpiderItem(response.meta.get("item")), selector=response)
        loader.add_value("rating", data.get("value"))
        return loader.load_item()
