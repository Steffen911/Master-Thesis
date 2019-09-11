import re
import json
import scrapy
import string
import hashlib
from crawler.items import Product


def get_start_urls():
    start_urls_loc = []
    base_url = "https://www.walmart.com/search/?page={}&ps=40&query={}"
    base_url_cat = "https://www.walmart.com/search/?cat_id={}&page={}&ps=40&query={}"
    categories = [1105910, 3944, 4096, 4104, 5426, 2636, 1229749]
    for q in string.ascii_lowercase[:26]:
        for i in range(1, 26):
            start_urls_loc.append(base_url.format(i, q))
            for cat in categories:
                start_urls_loc.append(base_url_cat.format(cat, i, q))
    return start_urls_loc


class WalmartComSpider(scrapy.Spider):
    name = "walmart_com"
    allowed_domains = ["walmart.com"]
    start_urls = get_start_urls()

    gtin_pattern = re.compile("data-gtin%3D%5C%220(\d{13})")

    def parse_product(self, response):
        breadcrumb = " > ".join(
            response.xpath("//li[@class = 'breadcrumb']/a/span/text()").getall()
        )
        identifiers = []
        for ld_info in response.xpath("//script[@id='item']/text()").getall():
            if "gtin" in ld_info:
                result = self.gtin_pattern.search(ld_info)
                identifiers.append({"gtin13": result.group(1)})
            item = json.loads(ld_info)
            if item["item"]["productId"]:
                identifiers.append({"productId": item["item"]["productId"]})
            if "sku" in ld_info:
                result = item["item"]["product"]["buyBox"]["products"][0]["skuId"]
                identifiers.append({"skuId": result})

        node = "node{}".format(hashlib.md5(response.body).hexdigest())
        yield Product(
            node=node,
            breadcrumb=breadcrumb,
            url=response.url,
            identifiers=identifiers,
            html=response.body,
        )

    def parse(self, response):
        # parse all products on the current page
        for href in response.xpath(
            "//a[contains(@class, 'product-title-link')]/@href"
        ).getall():
            if href:
                yield scrapy.Request(
                    response.urljoin(href), callback=self.parse_product
                )
