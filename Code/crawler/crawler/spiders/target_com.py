import json
import scrapy
import hashlib
from crawler.items import Product


class TargetComSpider(scrapy.Spider):
    name = "target_com"
    allowed_domains = ["target.com"]
    start_urls = ["https://www.target.com"]

    def parse(self, response):
        # parse product pages
        is_product = response.xpath('//h1[@data-test = "product-title"]/span/text()')
        if is_product:
            breadcrumb = " > ".join(
                response.xpath(
                    '//div[@data-test = "breadcrumb"]//a/span/text()'
                ).getall()
            )
            identifiers = []
            for ld_info in response.xpath(
                "//script[@type='application/ld+json']/text()"
            ).getall():
                item = json.loads(ld_info)
                for elem in item["@graph"]:
                    if elem["@type"] == "Product":
                        if elem["sku"]:
                            identifiers.append({"sku": elem["sku"]})
            node = "node{}".format(hashlib.md5(response.body).hexdigest())
            yield Product(
                node=node,
                breadcrumb=breadcrumb,
                url=response.url,
                identifiers=identifiers,
                html=response.body,
            )

        # follow all hyperlinks
        hyperlinks = response.xpath("//a/@href").getall()
        for next_page in hyperlinks:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)
