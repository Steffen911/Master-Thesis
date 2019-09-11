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


def _levenshtein(s1, s2, dummy=None):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(
                    1 + min((distances[i1], distances[i1 + 1], distances_[-1]))
                )
        distances = distances_
    return 1 - (distances[-1] / len(s2))


def _prepare_prediction(df):
    p1 = df.apply(lambda x: _levenshtein(x.taxonomy_l, x.taxonomy_r), axis=1)
    p2 = df.apply(
        lambda x: _levenshtein(_remove_last(x.taxonomy_l), x.taxonomy_r), axis=1
    )
    p3 = df.apply(
        lambda x: _levenshtein(x.taxonomy_l, _remove_last(x.taxonomy_r)), axis=1
    )
    return pd.concat([p1, p2, p3], axis=1)


class Levenshtein(Matcher):

    threshold = 1
    max_f1 = 0

    def __init__(self, labels):
        super(Levenshtein, self).__init__(labels)
        self.method = "levenshtein"

    def train(self, train, y_train):
        thresholds = np.linspace(0, 1, 10, endpoint=False)
        pred = _prepare_prediction(train)
        for t in thresholds:
            p = pred.apply(lambda x: _set_label(x, t), axis=1)
            f1 = get_aggregate_evaluation(
                self.labels,
                evaluate_prediction(
                    "{}-{}".format(self.method, t), self.labels, y_train, p
                ),
            )
            if f1 > self.max_f1:
                self.max_f1 = f1
                self.threshold = t
        logging.debug(
            "training found an optimum f1 of {} with threshold {}".format(
                self.max_f1, self.threshold
            )
        )

    def predict(self, test):
        pred = _prepare_prediction(test)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return pred

    def evaluate(self, test, y_test, print_output=False):
        return evaluate_prediction(
            self.method,
            self.labels,
            y_test,
            self.predict(test),
            print_output=print_output,
        )
