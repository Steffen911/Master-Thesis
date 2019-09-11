import itertools
import logging
import numpy as np
import pandas as pd
from matchers.matcher import Matcher
from nltk.corpus import wordnet as wn
from matchers.levenshtein import _levenshtein
from thesis.evaluation import evaluate_prediction, get_aggregate_evaluation
from thesis.utils import split_composite


def _longest_common_substring(wa, wb):
    (s1, s2) = (wa, wb) if len(wa) > len(wb) else (wb, wa)
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    lcs = s1[x_longest - longest : x_longest]
    return len(lcs) / len(s1)


def _get_related(s):
    related = [s]
    related.extend(s.hypernyms())
    related.extend(s.hyponyms())
    related.extend(s.part_meronyms())
    related.extend(s.part_holonyms())
    return related


def _disambiguate(w, ctx):
    z = wn.synsets(w)
    bestscore = 0
    bestsynset = None
    for s in z:
        sensescore = 0
        r = set(_get_related(s))
        p = itertools.product(r, ctx)
        for (sr, w) in p:
            sensescore += _longest_common_substring(sr.definition(), w)
        if sensescore > bestscore:
            bestscore = sensescore
            bestsynset = s
    return bestsynset


def _get_extended_term_set(ests_store, category):
    if category in ests_store:
        return ests_store[category]
    splitted = category.split(" > ")
    if len(splitted) == 0:
        return set()
    cat = split_composite(splitted[-1])
    ctx = set()
    # use everything but top- and last-level as context
    for x in splitted[1:-1]:
        ctx = ctx | split_composite(x)
    ests = set()
    for split in cat:
        ets = _disambiguate(split, ctx)
        if ets:
            ets = set([lemma.name() for lemma in ets.lemmas()])
            ets = ets | {split}
            ests = ests | ets
    ests_store[category] = ests
    return ests


def _semantic_match(ests, target, threshold):
    splitted = target.split(" > ")
    if len(splitted) == 0:
        return set()
    target = split_composite(splitted[-1])
    sub_set = True
    # experiment:
    # sub_set = False
    if not ests:
        return "disjoint"
    for split in ests:
        match_found = False
        p = itertools.product([split], target)
        for (split_syn, target_split) in p:
            edit_dist = _levenshtein(split_syn, target_split)
            if target_split in split_syn:
                match_found = True
            elif edit_dist >= threshold:
                match_found = True
        if not match_found:
            sub_set = False
        # experiment
        # if match_found:
        #     sub_set = True
    return "contained-in" if sub_set else "disjoint"


def _calc_match(row):
    label_l = row[0]
    label_r = row[1]
    if label_l == label_r == "contained-in":
        return "equal"
    if label_l == label_r == "disjoint":
        return "disjoint"
    if label_l == "contained-in":
        return "contains"
    if label_r == "contained-in":
        return "contained-in"
    return ValueError("invalid label combination")


def _prepare_prediction(df, _ests_store, t):
    p1 = df.apply(
        lambda x: _semantic_match(
            _get_extended_term_set(_ests_store, x.taxonomy_l), x.taxonomy_r, t
        ),
        axis=1,
    )
    p2 = df.apply(
        lambda x: _semantic_match(
            _get_extended_term_set(_ests_store, x.taxonomy_r), x.taxonomy_l, t
        ),
        axis=1,
    )
    return pd.concat([p1, p2], axis=1).apply(_calc_match, axis=1)


class Schema(Matcher):
    # https://github.com/nudge/schema/blob/master/schema/schema.py

    threshold = 1
    max_f1 = 0
    _ests_store = dict()

    def __init__(self, labels):
        super(Schema, self).__init__(labels)
        self.method = "schema"

    def train(self, train, y_train):
        thresholds = np.linspace(0, 1, 10, endpoint=False)
        for t in thresholds:
            p = _prepare_prediction(train, self._ests_store, t)
            f1 = get_aggregate_evaluation(
                self.labels, evaluate_prediction(self.method, self.labels, y_train, p)
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
        return _prepare_prediction(test, self._ests_store, self.threshold)

    def evaluate(self, test, y_test, print_output=False):
        pred = _prepare_prediction(test, self._ests_store, self.threshold)
        return evaluate_prediction(
            self.method, self.labels, y_test, pred, print_output=print_output
        )
