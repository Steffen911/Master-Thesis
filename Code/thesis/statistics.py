import re
import logging
import matplotlib.pyplot as plt
from thesis.experiments import tuples, get_goldstandard


def shorten_labels(lbl):
    return (
        "d"
        if lbl == "disjoint"
        else "ci"
        if lbl == "contained-in"
        else "c"
        if lbl == "contains"
        else "e"
        if lbl == "equal"
        else ValueError("Label not found")
    )


def split_taxonomy(taxonomy):
    if taxonomy == "" or taxonomy is None:
        return []
    for char in [">", "/", "\\\\"]:
        if re.search(char, taxonomy):
            return list(map(lambda x: x.strip(), re.split(char, taxonomy)))
    return [taxonomy]


def run(data_dir):
    gs = get_goldstandard(data_dir)
    count = gs.groupby("label").pld_l.count()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.bar(range(count.size), count.values)
    plt.xticks(range(count.size), count.index)
    ax.set_yscale("log")
    fig.show()
    logging.info(count)

    fig = plt.figure(figsize=(15, 15))
    for i, tup in enumerate(tuples):
        count = (
            gs[
                (
                    (gs.pld_l == tup[0]) & (gs.pld_r == tup[1])
                    | (gs.pld_l == tup[1]) & (gs.pld_r == tup[0])
                )
                & (
                    gs.label != "disjoint"
                )  # remove disjoint, since they usually are >> than the rest
            ]
            .groupby("label")
            .pld_l.count()
        )
        fig.add_subplot(3, 3, i + 1)
        plt.bar(range(count.size), count.values)
        plt.xticks(range(count.size), list(map(shorten_labels, count.index)))
        plt.title(tup)
    fig.show()

    gs["tax_length_l"] = gs.taxonomy_l.apply(lambda x: len(split_taxonomy(x)))
    gs["tax_length_r"] = gs.taxonomy_r.apply(lambda x: len(split_taxonomy(x)))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    txl = gs[(gs.label != "disjoint")].tax_length_l
    txr = gs[(gs.label != "disjoint")].tax_length_r
    txl.append(txr).hist(ax=ax)
    plt.title("depth of taxonomies")
    fig.show()
    logging.info(txl.append(txr).value_counts())

    logging.info("goldstandard entries for equal, contains and contained-in:")
    logging.info(
        "total number of entries: {}".format(gs[(gs.label != "disjoint")].pld_l.count())
    )


if __name__ == "__main__":
    run("../Data")
