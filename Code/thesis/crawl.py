import json
import logging
import requests
from lxml import html
import pandas as pd

mac_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"


def convert_exponent(number):
    # string of format d.ddE+dd
    if "E+" in str(number):
        # string of format d.ddE+dd
        return str(float(number))[0:-2]
    return number


def update_urls(url):
    url = url.replace("https", "http")
    if "bhphotovideo" in url:
        return url + "?fromDisList=y"
    if "bestbuy" in url and "?" in url:
        return url.split("?", 1)[0]
    if "bestbuy" in url and "%2525" in url:
        return url.split("%2525", 1)[0]
    if "ebay" in url and "%25253F" in url:
        return url.replace("%25253F", "?").replace("%25253", "=")
    if "cdw.com" in url:
        return url.split("%3F", 1)[0]
    if "newegg.com" in url:
        return url.replace("%3F", "?").replace("%3D", "=")
    return url


def extract_breadcrumbs(row, data_dir):
    if "E+" in row["upc"]:
        row["upc"] = convert_exponent(row["upc"])
    if "E+" in str(row["ean"]):
        row["ean"] = convert_exponent(row["ean"])
    result = {
        "identifiers": {
            "ean": row.get("ean"),
            "brand": row.get("brand"),
            "manufacturer": row.get("manufacturer"),
            "manufacturerNumber": row.get("manufacturerNumber"),
            "upc": row["upc"],
            "asins": row.get("asins"),
        },
        "breadcrumbs": {},
        "urls": {},
        "name": row["name"],
        "primaryCategories": row["primaryCategories"],
        "categories": row["categories"],
    }
    for url in set(map(update_urls, row["sources"])):
        try:
            headers = {"user-agent": mac_user_agent}
            cookies = dict(intl_splash="false")
            body = requests.get(url, headers=headers, cookies=cookies, timeout=20).text
            page = html.fromstring(body)
            logging.debug(f"crawled {url}")
            if "abt.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//ul[@class = "bread_crumbs"]//a/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["abt.com"] = url
                    result["breadcrumbs"]["abt.com"] = " > ".join(breadcrumbs)
            elif "officedepot.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//div[@id = "siteBreadcrumb"]//a/span/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["officedepot.com"] = url
                    result["breadcrumbs"]["officedepot.com"] = " > ".join(breadcrumbs)
            elif "overstock.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//ul[@class = "breadcrumbs"]//a/span/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["overstock.com"] = url
                    result["breadcrumbs"]["overstock.com"] = " > ".join(breadcrumbs)
            elif "kohls.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//span[@class = "pdp_breadcrumb_title"]//a/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["kohls.com"] = url
                    result["breadcrumbs"]["kohls.com"] = " > ".join(breadcrumbs)
            elif "amazon" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath(
                            '//div[@data-feature-name = "wayfinding-breadcrumbs"]//a/text()'
                        ),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["amazon"] = url
                    result["breadcrumbs"]["amazon"] = " > ".join(breadcrumbs)
            elif "bestbuy" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//nav[@aria-label = "breadcrumb"]//a/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["bestbuy"] = url
                    result["breadcrumbs"]["bestbuy"] = " > ".join(breadcrumbs)
            elif "bhphotovideo" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//ul[@id = "breadcrumbs"]//span/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["bhphotovideo"] = url
                    result["breadcrumbs"]["bhphotovideo"] = " > ".join(breadcrumbs)
            elif "walmart" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//nav[@aria-label = "breadcrumb"]//a//span/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["walmart"] = url
                    result["breadcrumbs"]["walmart"] = " > ".join(breadcrumbs)
            elif "frys.com" in url:
                if "Sorry," in body:
                    continue
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath(
                            '//ul[contains(@class, "frys-breadcrumb")]//a/text()'
                        ),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["frys.com"] = url
                    result["breadcrumbs"]["frys.com"] = " > ".join(breadcrumbs)
            elif "rei.com" in url:
                metadata = page.xpath(
                    '//script[@data-client-store = "product-metadata"]/text()'
                )[0]
                breadcrumbs = list(
                    map(
                        lambda x: x["label"].strip(),
                        json.loads(metadata)["breadcrumbCats"],
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["rei.com"] = url
                    result["breadcrumbs"]["rei.com"] = " > ".join(breadcrumbs)
            elif "cdw.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//ul[@class = "breadcrumbs"]//span/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["cdw.com"] = url
                    result["breadcrumbs"]["cdw.com"] = " > ".join(breadcrumbs)
            elif "newegg.com" in url:
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath('//ol[@class = "breadcrumb"]//a/text()'),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["newegg.com"] = url
                    result["breadcrumbs"]["newegg.com"] = " > ".join(breadcrumbs)
            elif "toysrus" in url:
                continue
            elif "homedepot" in url:
                continue
            elif "upccodesearch" in url:
                continue
            elif "barcodable" in url:
                continue
            elif "lowes" in url:
                continue
            elif "asus.com" in url:
                continue
            elif "lazada.sg" in url:
                continue
            elif "camelcamelcamel" in url:
                continue
            elif "lg.com" in url:
                continue
            elif "buy.com" in url:
                continue  # bestbuy is handled in a previous condition
            elif "kmart.com" in url:
                continue
            elif "ebay" in url:
                item_urls = page.xpath('//h1[@itemprop = "name"]//a/@href')
                if len(item_urls) > 0:
                    url = item_urls[0]
                    page = html.fromstring(
                        requests.get(
                            url, headers={"user-agent": mac_user_agent}, cookies=cookies
                        ).text
                    )
                breadcrumbs = list(
                    map(
                        lambda x: x.strip(),
                        page.xpath(
                            '//div[contains(@class, "breadcrumb")]//span/text()'
                        ),
                    )
                )
                if len(breadcrumbs) > 0:
                    result["urls"]["ebay"] = url
                    result["breadcrumbs"]["ebay"] = " > ".join(breadcrumbs)
            else:
                logging.warning(f"could not find extractor for {url}")
        except Exception as e:
            logging.error(f"error occurred: {e}")
    logging.info(f"extracted breadcrumbs: {result}")
    line = json.dumps(dict(result)) + "\n"
    with open(f"{data_dir}/products.json", "a") as f:
        f.write(line)
    return result


def run(data_dir):
    file = open(f"{data_dir}/products.json", "w")
    file.close()

    df = pd.read_csv(f"{data_dir}/electronic_products.csv")
    columns = [
        "prices.merchant",
        "sourceURLs",
        "categories",
        "primaryCategories",
        "name",
        "ean",
        "manufacturer",
        "manufacturerNumber",
        "brand",
        "upc",
        "asins",
    ]

    df = df[columns]
    df["sources"] = df["sourceURLs"].apply(lambda x: x.split(","))
    df = df[df["sources"].apply(lambda x: len(x) > 1)]

    df["breadcrumbs"] = df.apply(lambda x: extract_breadcrumbs(x, data_dir), axis=1)
    print(df.head())


def run_clothing(data_dir):
    file = open(f"{data_dir}/clothing_products.json", "w")
    file.close()

    with open(f"{data_dir}/clothing_products.json", mode="r") as f:
        i = 0
        for line in iter(f.readline, ""):
            if i % 100 == 0:
                logging.info(f"processed {i} lines")
            i += 1
            parsed = json.loads(line)
            parsed["sources"] = parsed["sourceURLs"]
            extract_breadcrumbs(parsed, data_dir)


if __name__ == "__main__":
    run("../../Data")
