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
from thesis.utils import embedding_cosine_sim


class Embeddings(Matcher):

    threshold = 1
    max_f1 = 0

    def __init__(self, labels):
        super(Embeddings, self).__init__(labels)
        self.method = "embedding"

    def _prepare_prediction(self, df):
        p1 = df.apply(
            lambda x: embedding_cosine_sim(x.taxonomy_l, x.taxonomy_r), axis=1
        )
        p2 = df.apply(
            lambda x: embedding_cosine_sim(_remove_last(x.taxonomy_l), x.taxonomy_r),
            axis=1,
        )
        p3 = df.apply(
            lambda x: embedding_cosine_sim(x.taxonomy_l, _remove_last(x.taxonomy_r)),
            axis=1,
        )
        return pd.concat([p1, p2, p3], axis=1)

    def train(self, train, y):
        thresholds = np.linspace(0, 1, 10, endpoint=False)
        pred = self._prepare_prediction(train)
        for t in thresholds:
            p = pred.apply(lambda x: _set_label(x, t), axis=1)
            f1 = get_aggregate_evaluation(
                self.labels,
                evaluate_prediction("{}-{}".format(self.method, t), self.labels, y, p),
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
        pred = self._prepare_prediction(test)
        pred = pred.apply(lambda x: _set_label(x, self.threshold), axis=1)
        return pred

    def evaluate(self, test, y_test, print_output):
        return evaluate_prediction(
            self.method,
            self.labels,
            y_test,
            self.predict(test),
            print_output=print_output,
        )
