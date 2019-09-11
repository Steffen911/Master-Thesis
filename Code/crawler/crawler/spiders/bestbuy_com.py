import json
import scrapy
import string
import hashlib
from crawler.items import Product


def parse_product(response):
    breadcrumb = " > ".join(
        response.xpath("//a[@data-track = 'Breadcrumb']/text()").getall()
    )
    identifiers = []
    for ld_info in response.xpath(
        "//script[@type='application/ld+json']/text()"
    ).getall():
        item = json.loads(ld_info)
        if type(item) is dict and item["@type"] == "Product":
            if item["sku"]:
                identifiers.append({"sku": item["sku"]})
            if item["gtin13"]:
                identifiers.append({"gtin13": item["gtin13"]})

    node = "node{}".format(hashlib.md5(response.body).hexdigest())
    yield Product(
        node=node,
        breadcrumb=breadcrumb,
        url=response.url,
        identifiers=identifiers,
        html=response.body,
    )


class BestBuyComSpider(scrapy.Spider):
    name = "bestbuy_com"
    allowed_domains = ["bestbuy.com"]
    start_urls = [
        "https://www.bestbuy.com/site/searchpage.jsp?intl=nosplash&st=" + x
        for x in string.ascii_lowercase[:26]
    ]

    def parse(self, response):
        # parse all products on the current page
        for href in response.xpath(
            "//h4[contains(@class, 'sku-header')]/a/@href"
        ).getall():
            if href:
                yield scrapy.Request(response.urljoin(href), callback=parse_product)

        # get the next page of search results
        next_page = response.xpath(
            "//a[contains(@class, 'ficon-caret-right')]/@href"
        ).get(default="")
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)
