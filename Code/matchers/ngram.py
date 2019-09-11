import logging
import numpy as np
import pandas as pd
from matchers.matcher import Matcher
from thesis.evaluation import (
    evaluate_prediction,
    _set_label,
    _remove_last,
    get_aggregate_evaluation,
)


def _ngrams(n, sequence):
    if n > len(sequence):
        return {sequence}
    sequence = list(sequence)
    count = max(0, len(sequence) - n + 1)
    return set(tuple(sequence[i : i + n]) for i in range(count))


def _ngram_similarity(s1, s2, n):
    n1 = _ngrams(n, s1)
    n2 = _ngrams(n, s2)
    if (min(len(s1), len(s2)) - n + 1) == 0:
        return 0
    return len(n1.intersection(n2)) / (min(len(s1), len(s2)) - n + 1)


def _prepare_prediction(df, n):
    p1 = df.apply(lambda x: _ngram_similarity(x.taxonomy_l, x.taxonomy_r, n), axis=1)
    p2 = df.apply(
        lambda x: _ngram_similarity(_remove_last(x.taxonomy_l), x.taxonomy_r, n), axis=1
    )
    p3 = df.apply(
        lambda x: _ngram_similarity(x.taxonomy_l, _remove_last(x.taxonomy_r), n), axis=1
    )
    return pd.concat([p1, p2, p3], axis=1)


class Ngram(Matcher):

    ngram = 0
    threshold = 1
    max_f1 = 0

    def __init__(self, labels):
        super(Ngram, self).__init__(labels)
        self.method = "ngram"

    def train(self, train, y_train):
        thresholds = np.linspace(0, 1, 10, endpoint=False)
        ngrams = range(2, 10)
        for n in ngrams:
            pred = _prepare_prediction(train, n)
            for t in thresholds:
                p = pred.apply(lambda x: _set_label(x, t), axis=1)
                f1 = get_aggregate_evaluation(
                    self.labels,
                    evaluate_prediction(
                        "{}-{}-{}".format(self.method, t, n), self.labels, y_train, p
                    ),
                )
                if f1 > self.max_f1:
                    self.max_f1 = f1
                    self.threshold = t
                    self.ngram = n
        logging.debug(
            "training found an optimum f1 of {} with threshold {} and ngram {}".format(
                self.max_f1, self.threshold, self.ngram
            )
        )

    def predict(self, test):
        pred = _prepare_prediction(test, self.ngram)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return pred

    def evaluate(self, test, y_test, print_output=False):
        pred = _prepare_prediction(test, self.ngram)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return evaluate_prediction(
            self.method, self.labels, y_test, pred, print_output=print_output
        )
