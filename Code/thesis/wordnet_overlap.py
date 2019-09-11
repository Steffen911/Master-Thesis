import pandas as pd
from itertools import chain
from thesis.utils import split_composite
from nltk.corpus import wordnet as wn


def get_set(class_label):
    labels = class_label.split(" > ")
    return set(chain.from_iterable(map(split_composite, labels)))


def run(data_dir):
    gs = pd.read_csv(f"{data_dir}/training.csv", sep="\t")[["taxonomy_l", "taxonomy_r"]]
    left = set(chain.from_iterable(gs["taxonomy_l"].apply(get_set)))
    right = set(chain.from_iterable(gs["taxonomy_r"].apply(get_set)))
    # only words with length greater 2
    words = left.union(right)
    words = set(filter(lambda x: len(x) > 2, words))
    in_wn = set()
    for word in words:
        if len(wn.synsets(word)) > 0:
            in_wn.add(word)
    print(len(in_wn) / len(words))


if __name__ == "__main__":
    run("../Data")
