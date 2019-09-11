import scrapy


class Product(scrapy.Item):
    node = scrapy.Field()
    breadcrumb = scrapy.Field()
    url = scrapy.Field()
    identifiers = scrapy.Field()
    html = scrapy.Field()
