import pandas as pd
from wdc.data_exploration import tuples


def run(data_dir):
    joined = pd.read_csv(f"{data_dir}/joined.csv", sep="\t")

    with open(f"{data_dir}/training.csv", "w") as f:
        print(
            '"pld_l"\t"taxonomy_l"\t"size_l"\t"pld_r"\t"taxonomy_r"\t"size_r"\t"size_int"\t"label"',
            file=f,
        )

    for pair in tuples:
        filtered = joined[(joined.pld_l == pair[0]) & (joined.pld_r == pair[1])]

        for tax_l in filtered.taxonomy_l.unique():
            cond_l = filtered.taxonomy_l == tax_l
            for tax_r in filtered.taxonomy_r.unique():
                cond_r = filtered.taxonomy_r == tax_r

                size_int = filtered[cond_l & cond_r].cluster_id.count()
                size_l = filtered[cond_l].cluster_id.count()
                size_r = filtered[cond_r].cluster_id.count()

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

                # also store the reverse label to increase GS size
                alt_label = (
                    "contains"
                    if label == "contained-in"
                    else "contained-in"
                    if label == "contains"
                    else label
                )

                with open(f"{data_dir}/training.csv", "a") as f:
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
    print("successfully created goldstandard of length {}".format(gs.label.count()))


if __name__ == "__main__":
    run("../../Data")
