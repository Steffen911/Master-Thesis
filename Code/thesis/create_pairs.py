import json
import logging
import collections
import pandas as pd
from thesis.crawl import convert_exponent


def is_unequal(row):
    return row.pld_l != row.pld_r


def handle_list(elem):
    if isinstance(elem, collections.Iterable):
        return ",".join(elem)
    return elem


def clean_category(category):
    # cleanup paths like "BestBuy > Wearable Technology > Smart ... > Product Details"
    return " > ".join(
        list(
            filter(
                lambda x: x != "Product Details",
                filter(lambda x: x != "Best Buy", category.split(" > ")),
            )
        )
    )


def create_pairs(data_dir):
    data = []
    with open(f"{data_dir}/products.json", mode="r") as f:
        for line in iter(f.readline, ""):
            parsed = json.loads(line)
            for key, value in parsed["breadcrumbs"].items():
                elem = {
                    "taxonomy": clean_category(value),
                    "pld": key,
                    "categories": handle_list(parsed["categories"]),
                    "ean": handle_list(convert_exponent(parsed["identifiers"]["ean"])),
                    "manufacturerNumber": parsed["identifiers"]["manufacturerNumber"],
                    "upc": handle_list(parsed["identifiers"]["upc"]),
                    "asins": handle_list(parsed["identifiers"]["asins"]),
                    "url": parsed["urls"][key],
                }
                data.append(elem)

    df = pd.DataFrame(data).drop_duplicates(subset=["pld", "upc"])
    joined = df.join(
        df.set_index("upc"), on="upc", how="inner", lsuffix="_l", rsuffix="_r"
    )
    logging.info("joined dataframe")
    joined = joined[joined.apply(is_unequal, axis=1)]
    logging.info("filtered unnecessary self join tuples")
    joined.to_csv(f"{data_dir}/products_joined.csv", sep="\t")
