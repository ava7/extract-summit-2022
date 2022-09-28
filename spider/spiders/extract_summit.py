import json

import scrapy
from scrapy.loader import ItemLoader

from spider.items import SpiderItem


class ExtractSummitSpider(scrapy.Spider):
    name = 'extract_summit'
    allowed_domains = ['extract-summit-kokb7ng7-5umjfyjn4a-ew.a.run.app']
    start_urls = ['https://extract-summit-kokb7ng7-5umjfyjn4a-ew.a.run.app/']

    def parse(self, response):
        url = response.urljoin(response.css("li:nth-child(2) .external::attr(href)").get())
        return response.follow(url, callback=self.parse_category)

    def parse_category(self, response):
        for item in response.css(".gtco-practice-area-item"):
            yield response.follow(item.css("a::attr(href)").get(), callback=self.parse_item)

        yield response.follow(response.css('.row[align="center"] a:last-child::attr(href)').get(),
                              callback=self.parse_category)

    def parse_item(self, response):
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

        loader.add_css("rating", ".price::text")
        loader.add_value("rating", data.get("rating"))
        loader.add_xpath("rating", "//*[contains(text(),'Rating')]/span/text()")

        loader.add_css("phone", 'script:contains("cyphered_phone")::text', re='from\(\"(.+)?\"')

        rating_url = response.css(".price::attr(data-price-url)").get()
        if not any(loader.get_collected_values("rating")) and rating_url:
            return response.follow(rating_url,
                                   callback=self.extract_stock,
                                   meta={"item": loader.load_item()})

        yield loader.load_item()

    def extract_stock(self, response):
        data = json.loads(response.text)
        loader = ItemLoader(item=SpiderItem(response.meta.get("item")), selector=response)
        loader.add_value("rating", data.get("value"))
        return loader.load_item()
