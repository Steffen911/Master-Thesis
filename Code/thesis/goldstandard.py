import logging
import pandas as pd

tuples = [
    ("amazon", "bestbuy"),
    ("amazon", "bhphotovideo"),
    ("amazon", "cdw.com"),
    ("amazon", "walmart"),
    ("amazon", "frys.com"),
    ("amazon", "ebay"),
    ("amazon", "newegg.com"),
    ("amazon", "officedepot.com"),
    ("amazon", "overstock.com"),
    ("amazon", "rei.com"),
    ("amazon", "abt.com"),
    ("amazon", "kohls.com"),
    ("bestbuy", "walmart"),
    ("bestbuy", "bhphotovideo"),
    ("bestbuy", "frys.com"),
    ("bestbuy", "cdw.com"),
    ("bestbuy", "ebay"),
    ("bestbuy", "newegg.com"),
    ("bestbuy", "officedepot.com"),
    ("bestbuy", "overstock.com"),
    ("bestbuy", "rei.com"),
    ("bestbuy", "abt.com"),
    ("bestbuy", "kohls.com"),
    ("walmart", "ebay"),
    ("walmart", "frys.com"),
    ("walmart", "cdw.com"),
    ("walmart", "bhphotovideo"),
    ("walmart", "newegg.com"),
    ("walmart", "officedepot.com"),
    ("walmart", "overstock.com"),
    ("walmart", "rei.com"),
    ("walmart", "abt.com"),
    ("walmart", "kohls.com"),
    ("ebay", "bhphotovideo"),
    ("ebay", "cdw.com"),
    ("ebay", "frys.com"),
    ("ebay", "newegg.com"),
    ("ebay", "officedepot.com"),
    ("ebay", "overstock.com"),
    ("ebay", "rei.com"),
    ("ebay", "abt.com"),
    ("ebay", "kohls.com"),
    ("cdw.com", "bhphotovideo"),
]


def run(data_dir):
    joined = pd.read_csv(f"{data_dir}/products_joined.csv", sep="\t")

    with open(f"{data_dir}/training.csv", "w") as f:
        print(
            '"pld_l"\t"taxonomy_l"\t"size_l"\t"pld_r"\t"taxonomy_r"\t"size_r"\t"size_int"\t"label"',
            file=f,
        )

    for pair in tuples:
        i = 0
        filtered = joined[(joined.pld_l == pair[0]) & (joined.pld_r == pair[1])]
        logging.info(f"processing tuple {pair}")
        with open(f"{data_dir}/training.csv", "a") as f:
            for tax_l in filtered.taxonomy_l.unique():
                cond_l = filtered.taxonomy_l == tax_l
                for tax_r in filtered.taxonomy_r.unique():
                    cond_r = filtered.taxonomy_r == tax_r

                    size_int = filtered[cond_l & cond_r].upc.count()
                    size_l = filtered[cond_l].upc.count()
                    size_r = filtered[cond_r].upc.count()

                    label = (
                        "disjoint"
                        if size_int == 0
                        else "equal"
                        if size_int == size_l == size_r
                        else "contained-in"
                        if size_int == size_l
                        else "contains"
                        if size_int == size_r
                        else "partial-intersection"
                    )

                    if label == "partial-intersection":
                        continue

                    i += 1
                    if i % 2000 == 0:
                        logging.debug(
                            f"inserted {i} entries into goldstandard for tuple {pair}"
                        )

                    # also store the reverse label to increase GS size
                    alt_label = (
                        "contains"
                        if label == "contained-in"
                        else "contained-in"
                        if label == "contains"
                        else label
                    )

                    print(
                        '"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"'.format(
                            pair[0],
                            tax_l,
                            size_l,
                            pair[1],
                            tax_r,
                            size_r,
                            size_int,
                            label,
                        ),
                        file=f,
                    )
                    print(
                        '"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"\t"{}"'.format(
                            pair[1],
                            tax_r,
                            size_r,
                            pair[0],
                            tax_l,
                            size_l,
                            size_int,
                            alt_label,
                        ),
                        file=f,
                    )

    gs = pd.read_csv(f"{data_dir}/training.csv", sep="\t")
    logging.info(f"successfully created goldstandard of length {gs.label.count()}")


if __name__ == "__main__":
    run("../Data")
