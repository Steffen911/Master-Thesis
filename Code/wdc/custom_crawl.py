import json
import pandas as pd


# Process the results from scrapy crawler


def extract_data(data_dir, crawler_name, pld):
    with open(f"{data_dir}/crawls/{crawler_name}.json", mode="r") as f:
        for line in iter(f.readline, ""):
            parsed = json.loads(line)
            with open(f"{data_dir}/custom_crawl.csv", "a") as o:
                for tup in parsed["identifiers"]:
                    key = next(iter(tup))
                    print(
                        f'"{parsed["node"]}"\t"{parsed["url"]}"\t"{tup[key]}"\t"{pld}"\t"{parsed["breadcrumb"]}"',
                        file=o,
                    )

        print(f"completed processing of {pld}")


def run(data_dir):
    with open(f"{data_dir}/custom_crawl.csv", "w") as f:
        print('"nodeID"\t"url"\t"identifier"\t"pld"\t"breadcrumb"', file=f)

    extract_data(data_dir, "walmart_com", "walmart")
    extract_data(data_dir, "bestbuy_com", "bestbuy")

    df = pd.read_csv(f"{data_dir}/custom_crawl.csv", sep="\t")
    df["identifier"] = df["identifier"].apply(lambda x: f"{x}".strip().lstrip("0"))
    walmart = df[df.pld == "walmart"]
    bestbuy = df[df.pld == "bestbuy"]

    merged = pd.merge(
        walmart, bestbuy, on="identifier", how="inner", suffixes=("_w", "_b")
    ).drop_duplicates(subset=["identifier", "nodeID_w", "nodeID_b"])

    print(
        merged["breadcrumb_w"].value_counts()[
            merged["breadcrumb_w"].value_counts() > 15
        ]
    )
    print(
        merged["breadcrumb_b"].value_counts()[
            merged["breadcrumb_b"].value_counts() > 15
        ]
    )


if __name__ == "__main__":
    run("../../Data")
