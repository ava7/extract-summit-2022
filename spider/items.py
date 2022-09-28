# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose

extract_image_id = MapCompose(lambda v: v.split("/")[-1].split(".")[0])
convert_phone = MapCompose(lambda cryptic_phone: ''.join(map(chr, [ord(letter)-16 for letter in cryptic_phone])))


class SpiderItem(scrapy.Item):
    # define the fields for your item here like:
    item_id = scrapy.Field(output_processor=TakeFirst())
    name = scrapy.Field(output_processor=TakeFirst())
    image_id = scrapy.Field(input_processor=extract_image_id, output_processor=TakeFirst())
    rating = scrapy.Field(output_processor=TakeFirst())
    phone = scrapy.Field(input_processor=convert_phone, output_processor=TakeFirst())
