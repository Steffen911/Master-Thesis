# Get the data and store it in "../Data"
# Download and unpack http://data.dws.informatik.uni-mannheim.de/largescaleproductcorpus/data/offers_english.json.gz
# Download and unpack http://data.dws.informatik.uni-mannheim.de/largescaleproductcorpus/data/idclusters.json.gz
# Download http://data.dws.informatik.uni-mannheim.de/structureddata/2017-12/quads/classspecific/schema_Product.gz

# Uncomment and execute the next two lines to create the data .csv's
# %run extract_taxonomies.py
# %run extract_products.py
# %run extract_id_clusters.py

# Load and prepare data

# First, we load all input datasets into spark, clean them up and join them.
# This will result in a dataframe that contains products in the clothing or electronics domain
# and are assigned to a cluster from the WDC training corpus.
#
# Finally, we will perform a self-join of the data to retrieve product-pairs that are
# in the same cluster.
# We will store those pairs in a dataframe and save it as a file.

from .load_prepare import run

run("../../Data")

# Data Exploration

# Next, we explore the data and search for PLD-Pairs that have lots of products in common and offer
# some interesting, i.e. long, taxonomies.
# We save the PLD-Pairs that we want to explore further and look at some sample taxonomies from
# all pairs.

from .data_exploration import run

run("../../Data")

# Gold Standard Creation

# We have multiple PLD pairs that contain interesting taxonomies.
# As the next step, we use an instance-based method to detect if a taxonomy is equal, contained-in,
# contains or disjoint with another.
#     We will store this in another file, our goldstandard.
#
# Let $A$ and $B$ be sets of taxonomies from two different PLDs.
# We say that
# - $A$ equals $B$, iff $A \cap B = A = B$
# - $A$ contains $B$, iff $A \cap B = B$
# - $A$ is contained in $B$, iff $A \cap B = A$
# - $A$ and $B$ are disjoint, iff $A \cap B = \emptyset$

from .create_goldstandard import run

run("../../Data")

# Goldstandard Statistics

import pandas as pd
import matplotlib.pyplot as plt

gs = pd.read_csv("../Data/training.csv", sep="\t")
count = gs.groupby("label").pld_l.count()
fig = plt.figure()
ax = fig.add_subplot(111)
plt.bar(range(count.size), count.values)
plt.xticks(range(count.size), count.index)
ax.set_yscale("log")
count

from .data_exploration import tuples


def shorten_labels(lbl):
    return (
        "d"
        if lbl == "disjoint"
        else "ci"
        if lbl == "contained-in"
        else "c"
        if lbl == "contains"
        else "pi"
        if lbl == "partial-intersection"
        else "e"
        if lbl == "equal"
        else ValueError("Label not found")
    )


fig = plt.figure(figsize=(10, 11))
for i, tup in enumerate(tuples):
    count = (
        gs[
            (gs.pld_l == tup[0]) & (gs.pld_r == tup[1])
            | (gs.pld_l == tup[1]) & (gs.pld_r == tup[0])
        ]
        .groupby("label")
        .pld_l.count()
    )
    ax = fig.add_subplot(3, 3, i + 1)
    plt.bar(range(count.size), count.values)
    plt.xticks(range(count.size), list(map(shorten_labels, count.index)))
    plt.title(tup)
    ax.set_yscale("log")

# Taxonomy Depth Histograms

from .data_exploration import split_taxonomy

filter_no_rel = (gs.label != "disjoint") & (gs.label != "partial-intersection")
gs["tax_length_l"] = gs.taxonomy_l.apply(lambda x: len(split_taxonomy(x)))
gs["tax_length_r"] = gs.taxonomy_r.apply(lambda x: len(split_taxonomy(x)))

fig = plt.figure()
ax = fig.add_subplot(111)
txl = gs[filter_no_rel].tax_length_l
txr = gs[filter_no_rel].tax_length_r
txl.append(txr).hist(ax=ax)
plt.title("depth of taxonomies")
txl.append(txr).value_counts()

pld_list = set(y for x in tuples for y in x)
fig = plt.figure(figsize=(10, 14))
split_l = int(len(pld_list) / 2)
split_r = len(pld_list) - split_l

for i, pld in enumerate(pld_list):
    filter_cond = (gs.pld_l == pld) | (gs.pld_r == pld)
    ax = fig.add_subplot(split_l, split_r, i + 1)
    txl = gs[filter_cond & filter_no_rel].tax_length_l
    txr = gs[filter_cond & filter_no_rel].tax_length_r
    txl.append(txr).hist(ax=ax)
    plt.title(pld)

# Bucket Size

fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(131)
gs.size_l.hist(ax=ax, bins=10)
ax.set_yscale("log")
plt.title("size of left bucket")
ax = fig.add_subplot(132)
gs.size_r.hist(ax=ax, bins=10)
ax.set_yscale("log")
plt.title("size of right bucket")
ax = fig.add_subplot(133)
gs.size_int.hist(ax=ax, bins=10)
ax.set_yscale("log")
plt.title("size of intersection")

print("goldstandard entries for equal, contains and contained-in:")
print("total number of entries: {}".format(gs[filter_no_rel].pld_l.count()))
print(
    "number of entries where one product was used for decision: {}".format(
        gs[((gs.size_l == 1) | (gs.size_r == 1)) & filter_no_rel].pld_l.count()
    )
)
print(
    "number of entries where two products were used for decision: {}".format(
        gs[((gs.size_l == 2) | (gs.size_r == 2)) & filter_no_rel].pld_l.count()
    )
)

# Baseline Methods

# In this section we will run some base line methods on the goldstandard to validate our assumption
# that basic methods like Levenshtein are insufficient.
# Since we got 7 PLD pairs, we will use 5 for training and k-fold CV and 2 for testing (i.e. getting
# an estimate for the performance on previously unseen data.

import pandas as pd
from matchers.ngram import Ngram
from matchers.schema import Schema
from matchers.levenshtein import Levenshtein

# split the gold standard
gs = pd.read_csv("../Data/training.csv", sep="\t")

train_cond = (
    ((gs.pld_l == "cdw") & (gs.pld_r == "pssl"))
    | ((gs.pld_l == "cdw") & (gs.pld_r == "printerland"))
    | ((gs.pld_l == "equipboard") & (gs.pld_r == "pssl"))
    | ((gs.pld_l == "ontimesupplies") & (gs.pld_r == "cdw"))
    | ((gs.pld_l == "printerland") & (gs.pld_r == "cdw"))
    | ((gs.pld_l == "pssl") & (gs.pld_r == "equipboard"))
)  # | \
# ((gs.pld_l == "budsgunshop") & (gs.pld_r == "sportsmansguide"))

test_cond = (
    ((gs.pld_l == "cdw") & (gs.pld_r == "ontimesupplies"))
    | ((gs.pld_l == "pssl") & (gs.pld_r == "yandasmusic"))
    | ((gs.pld_l == "pssl") & (gs.pld_r == "cdw"))
    | ((gs.pld_l == "yandasmusic") & (gs.pld_r == "pssl"))
)

train = gs[train_cond]
test = gs[test_cond]

labels = ["equal", "contains", "contained-in", "disjoint"]

ls = Levenshtein(labels)
ls.train(train, train.label)
ls.evaluate(test, test.label, print_output=True)

n = Ngram(labels)
n.train(train, train.label)
n.evaluate(test, test.label, print_output=True)

s = Schema(labels)
s.train(train, train.label)
s.evaluate(test, test.label, print_output=True)
