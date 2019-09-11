import re
import pandas as pd


tuples = [
    # ("budsgunshop", "sportsmansguide"),
    ("cdw", "pssl"),
    ("cdw", "ontimesupplies"),
    ("cdw", "printerland"),
    ("equipboard", "pssl"),
    ("pssl", "yandasmusic"),
]


def split_taxonomy(taxonomy):
    if taxonomy == "" or taxonomy is None:
        return []
    for char in [">", "/", "\\\\"]:
        if re.search(char, taxonomy):
            return list(map(lambda x: x.strip(), re.split(char, taxonomy)))
    return [taxonomy]


def get_avg_tax_length(tup):
    a = len(split_taxonomy(tup.taxonomy_l))
    b = len(split_taxonomy(tup.taxonomy_r))
    return (a + b) / 2


def run(data_dir):
    joined = pd.read_csv(f"{data_dir}/joined.csv", sep="\t")

    joined["tax_length_l"] = joined.taxonomy_l.apply(lambda x: len(split_taxonomy(x)))
    joined["tax_length_r"] = joined.taxonomy_r.apply(lambda x: len(split_taxonomy(x)))

    sorted_df = joined.groupby(["pld_l", "pld_r"]).agg("count")
    threshold = 3
    min_matches = 50
    for item in sorted_df.cluster_id.iteritems():
        if item[1] < min_matches:
            continue
        pld1 = item[0][0]
        pld2 = item[0][1]
        filtered = joined[(joined.pld_l == pld1) & (joined.pld_r == pld2)]
        res = filtered.apply(get_avg_tax_length, axis=1).mean() >= threshold
        if res:
            size1 = joined[joined.pld_l == pld1].tax_length_l.mean()
            size2 = joined[joined.pld_r == pld2].tax_length_r.mean()
            print(
                "{} - {}: Size: {}, Avg depth: {}, dep_l: {}, dep_r: {}".format(
                    pld1, pld2, item[1], res, size1, size2
                )
            )

    for pair in tuples:
        print(
            "\n-------------------------------------------\n{} - {}".format(
                pair[0], pair[1]
            )
        )
        filtered = joined[(joined.pld_l == pair[0]) & (joined.pld_r == pair[1])]
        print("Number of matching products: {}".format(filtered.cluster_id.count()))
        # print(filtered[["taxonomy_l", "taxonomy_r"]].head())


if __name__ == "__main__":
    run("../../Data")
