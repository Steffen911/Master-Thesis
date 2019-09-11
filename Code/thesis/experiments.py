import logging
import itertools
import numpy as np
import pandas as pd
from matchers.ml import NaiveBayes, AdaBoost, SGD, MLP
from matchers.ngram import Ngram
from matchers.s_match import SMatch
from matchers.schema import Schema
from matchers.levenshtein import Levenshtein
from matchers.path_distance import PathDistance
from matchers.embeddings import Embeddings

tuples = [
    ("amazon", "walmart"),
    ("amazon", "ebay"),
    ("bestbuy", "walmart"),
    ("newegg.com", "walmart"),
    ("overstock.com", "walmart"),
    ("amazon", "bestbuy"),
    ("bestbuy", "ebay"),
    ("ebay", "walmart"),
]


def generate_corner_cases(gs):
    """
    generate_corner_cases takes an instance of a goldstandard dataframe and generates additional disjoint cases
    that are close.
    It takes two examples from a single taxonomy that only diverge on the last element in the class-label and
    adds them as a disjoint case.
    Generated corner-cases are identified by a size_int of -1.
    """
    for t in tuples:
        class_l = gs[gs["pld_l"] == t[0]]["taxonomy_l"].unique()
        class_l = list(map(lambda x: (" > ".join(x.split(" > ")[:-1]), x), class_l))
        matches_l = list(
            filter(
                lambda x: x[0][0] == x[1][0] and x[0][1] != x[1][1],
                itertools.product(class_l, class_l),
            )
        )
        new_l = pd.DataFrame(
            map(
                lambda x: pd.Series(
                    [t[0], x[0][1], -1, t[1], x[1][1], -1, -1, "disjoint"],
                    index=gs.columns,
                ),
                matches_l,
            )
        )

        class_r = gs[gs["pld_r"] == t[1]]["taxonomy_r"].unique()
        class_r = list(map(lambda x: (" > ".join(x.split(" > ")[:-1]), x), class_r))
        matches_r = list(
            filter(
                lambda x: x[0][0] == x[1][0] and x[0][1] != x[1][1],
                itertools.product(class_r, class_r),
            )
        )
        new_r = pd.DataFrame(
            map(
                lambda x: pd.Series(
                    [t[0], x[0][1], -1, t[1], x[1][1], -1, -1, "disjoint"],
                    index=gs.columns,
                ),
                matches_r,
            )
        )

        gs = pd.concat([gs, new_l, new_r])

    return gs


def get_goldstandard(data_dir):
    gs_pos = pd.read_csv(f"{data_dir}/goldstandard_positive.csv", sep="\t")
    gs_pos = gs_pos[~gs_pos["manual"].isna()]
    gs = pd.read_csv(f"{data_dir}/training.csv", sep="\t")
    gs = generate_corner_cases(gs)
    # fill manual field with label for negative cases
    gs["manual"] = gs["label"]
    gs = pd.concat(
        [
            gs_pos,  # manually verified positive examples
            gs[(gs["size_int"] == -1)].sample(
                frac=0.1, random_state=42
            ),  # generates corner-cases
            gs[(gs["size_int"] == 0)].sample(
                frac=0.005, random_state=42
            ),  # sample of actual negatives
        ]
    )
    # use manual field as label
    gs["label"] = gs["manual"]
    return gs


def run(data_dir):
    gs = get_goldstandard(data_dir)

    # evaluate results
    labels = ["equal", "contains", "contained-in"]

    res_levenshtein = []
    res_ngram = []
    res_pd_levenshtein = []
    res_pd_ngram = []
    res_schema = []
    res_embedding = []
    res_adaboost = []
    res_adaboost_emb = []
    res_nb = []
    res_sgd = []
    res_sgd_emb = []
    res_smatch = []
    res_mlp = []

    logging.info("starting evaluation")
    for i in range(len(tuples)):
        train_tuples = [x for j, x in enumerate(tuples) if i != j]
        test_tuples = [tuples[i]]

        train_cond = list(
            map(
                lambda x: f"((gs['pld_l'] == '{x[0]}') & (gs['pld_r'] == '{x[1]}'))",
                train_tuples,
            )
        )
        train = gs[eval(f"({' | '.join(train_cond)})")]

        test_cond = list(
            map(
                lambda x: f"((gs['pld_l'] == '{x[0]}') & (gs['pld_r'] == '{x[1]}'))",
                test_tuples,
            )
        )
        test = gs[eval(f"({' | '.join(test_cond)})")]

        logging.info("creating levenshtein model")
        m = Levenshtein(labels)
        m.train(train, train.label)
        res_levenshtein.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("creating ngram model")
        m = Ngram(labels)
        m.train(train, train.label)
        res_ngram.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("creating path distance model with levenshtein")
        m = PathDistance(labels, use_ngram=False)
        m.train(train, train.label)
        res_pd_levenshtein.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("creating path distance model with ngram")
        m = PathDistance(labels, use_ngram=True)
        m.train(train, train.label)
        res_pd_ngram.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("creating schema model")
        m = Schema(labels)
        m.train(train, train.label)
        res_schema.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running embedding model")
        m = Embeddings(labels)
        m.train(train, train.label)
        res_embedding.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running adaboost bow model")
        m = AdaBoost(labels, embedding=False)
        m.train(train, train.label)
        res_adaboost.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running adaboost embedding model")
        m = AdaBoost(labels, embedding=True)
        m.train(train, train.label)
        res_adaboost_emb.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running naive bayes model")
        m = NaiveBayes(labels)
        m.train(train, train.label)
        res_nb.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running sgd bow model")
        m = SGD(labels, embedding=False)
        m.train(train, train.label)
        res_sgd.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running sgd embedding model")
        m = SGD(labels, embedding=True)
        m.train(train, train.label)
        res_sgd_emb.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running mlp model")
        m = MLP(labels)
        m.train(train, train.label)
        res_mlp.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info("running s-match model")
        m = SMatch(labels)
        res_smatch.append(m.evaluate(test, test.label, print_output=False))
        m.print_prediction(data_dir, test)

        logging.info(f"finished evaluation {i + 1}/{len(tuples)}")

    logging.info("\n\nevaluating results from nested cross validation")
    results = [
        "res_levenshtein",
        "res_ngram",
        "res_pd_levenshtein",
        "res_pd_ngram",
        "res_schema",
        "res_embedding",
        "res_adaboost",
        "res_nb",
        "res_sgd",
        "res_smatch",
        "res_adaboost_emb",
        "res_sgd_emb",
        "res_mlp",
    ]

    for result in results:
        logging.info(f"average scores for {result}")
        equal_precision = 0
        equal_recall = 0
        equal_f1 = 0
        contains_precision = 0
        contains_recall = 0
        contains_f1 = 0
        contained_in_precision = 0
        contained_in_recall = 0
        contained_in_f1 = 0
        confusion_matrix = np.zeros(shape=(4, 4))
        for i, entry in enumerate(eval(result)):
            logging.debug(f"results for {result} on {tuples[i]}: {entry}")
            equal_precision += entry["equal"]["precision"]
            equal_recall += entry["equal"]["recall"]
            equal_f1 += entry["equal"]["f1"]
            contains_precision += entry["contains"]["precision"]
            contains_recall += entry["contains"]["recall"]
            contains_f1 += entry["contains"]["f1"]
            contained_in_precision += entry["contained-in"]["precision"]
            contained_in_recall += entry["contained-in"]["recall"]
            contained_in_f1 += entry["contained-in"]["f1"]
            confusion_matrix += entry["confusion_matrix"]
        n = len(results)
        logging.info(
            f"{result}, equal -> precision: {equal_precision / n}, recall: {equal_recall / n}, f1: {equal_f1 / n}"
        )
        logging.info(
            f"{result}, contains -> precision: {contains_precision / n}, recall: {contains_recall / n}, f1: {contains_f1 / n}"
        )
        logging.info(
            f"{result}, contained-in -> precision: {contained_in_precision / n}, recall: {contained_in_recall / n}, f1: {contained_in_f1 / n}"
        )
        logging.info(f"{result} confusion matrix: \n{confusion_matrix}\n\n")
