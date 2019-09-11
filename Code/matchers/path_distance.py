import logging
import numpy as np
import pandas as pd
from matchers.levenshtein import _levenshtein
from matchers.ngram import _ngram_similarity
from matchers.matcher import Matcher
from thesis.evaluation import (
    evaluate_prediction,
    _set_label,
    _remove_last,
    get_aggregate_evaluation,
)


class PathDistance(Matcher):

    _lambda = 0
    ngram = 0
    threshold = 1
    max_f1 = 0
    use_ngram = False

    def __init__(self, labels, use_ngram=False):
        super(PathDistance, self).__init__(labels)
        self.method = "path_distance"
        self.use_ngram = use_ngram
        self.distance_fun = _ngram_similarity if use_ngram else _levenshtein
        self.method += "_ngram" if use_ngram else "_levenshtein"

    def _path_distance(self, t1, t2, _lambda, n):
        if len(t1) == 0 or len(t2) == 0:
            return 0
        return _lambda * self.distance_fun(t1[-1], t2[-1], n) + (
            1 - _lambda
        ) * self._path_distance(t1[:-1], t2[:-1], _lambda, n)

    def _prepare_prediction(self, df, _lambda, n):
        p1 = df.apply(
            lambda x: self._path_distance(
                x.taxonomy_l.split(" > "), x.taxonomy_r.split(" > "), _lambda, n
            ),
            axis=1,
        )
        p2 = df.apply(
            lambda x: self._path_distance(
                _remove_last(x.taxonomy_l).split(" > "),
                x.taxonomy_r.split(" > "),
                _lambda,
                n,
            ),
            axis=1,
        )
        p3 = df.apply(
            lambda x: self._path_distance(
                x.taxonomy_l.split(" > "),
                _remove_last(x.taxonomy_r).split(" > "),
                _lambda,
                n,
            ),
            axis=1,
        )
        return pd.concat([p1, p2, p3], axis=1)

    def train(self, train, y_train):
        thresholds = np.linspace(0, 1, 10, endpoint=False)
        lambdas = np.linspace(0, 1, 10, endpoint=False)
        ngrams = range(2, 10) if self.use_ngram else [0]
        for _lambda in lambdas:
            for n in ngrams:
                pred = self._prepare_prediction(train, _lambda, n)
                for t in thresholds:
                    p = pred.apply(lambda x: _set_label(x, t), axis=1)
                    f1 = get_aggregate_evaluation(
                        self.labels,
                        evaluate_prediction(
                            "{}-{}-{}-{}".format(self.method, t, _lambda, n),
                            self.labels,
                            y_train,
                            p,
                        ),
                    )
                    if f1 > self.max_f1:
                        self.max_f1 = f1
                        self.threshold = t
                        self._lambda = _lambda
                        self.ngram = n
        logging.debug(
            f"training found an optimum f1 of {self.max_f1} with threshold {self.threshold} and lambda {self._lambda} and ngram {self.ngram}"
        )

    def predict(self, test):
        pred = self._prepare_prediction(test, self._lambda, self.ngram)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return pred

    def evaluate(self, test, y_test, print_output=False):
        pred = self._prepare_prediction(test, self._lambda, self.ngram)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return evaluate_prediction(
            self.method, self.labels, y_test, pred, print_output=print_output
        )
