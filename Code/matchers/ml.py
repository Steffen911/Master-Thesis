import numpy as np
import pandas as pd
from matchers.matcher import Matcher
from imblearn.over_sampling import SMOTE
from thesis.evaluation import evaluate_prediction
from matchers.levenshtein import _levenshtein
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import SGDClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import AdaBoostClassifier
from sklearn.feature_extraction.text import CountVectorizer
from thesis.utils import get_class_vector


class ML(Matcher):
    def __init__(self, labels, classifier, parameter, embedding=True):
        super(ML, self).__init__(labels)
        self.method = "ml"
        self.vectorizer = CountVectorizer()
        self.clf = classifier
        self.parameter = parameter
        self.embedding = embedding

    def _transform_df(self, x):
        if self.embedding:
            return pd.Series(
                np.concatenate(
                    [
                        get_class_vector(x["taxonomy_l"]),
                        get_class_vector(x["taxonomy_r"]),
                    ]
                )
            )
        return pd.Series(
            np.concatenate(
                [
                    self.vectorizer.transform([x["taxonomy_l"]]).toarray(),
                    self.vectorizer.transform([x["taxonomy_r"]]).toarray(),
                ],
                axis=1,
            )[0]
        )

    def train(self, train, y):
        gs_clf = GridSearchCV(self.clf, self.parameter, n_jobs=-1)
        docs = pd.concat([train.taxonomy_l, train.taxonomy_r])
        self.vectorizer.fit(docs)
        X = train.apply(self._transform_df, axis=1)
        X_resampled, y_resampled = SMOTE(random_state=42).fit_resample(X, y)
        self.clf = gs_clf.fit(X_resampled, y_resampled)

    def predict(self, test):
        X = test.apply(self._transform_df, axis=1)
        return self.clf.predict(X)

    # enable for SGD experiment
    # def predict(self, test):
    #     X = test.apply(self._transform_df, axis=1)
    #     p1 = test.apply(lambda x: _levenshtein(x.taxonomy_l, x.taxonomy_r), axis=1)
    #     p2 = self.clf.predict(X)
    #
    #     y_pred = []
    #     for i, v in enumerate(p2):
    #         y_pred.append(v if p1.iloc[i] > 0.3 else "disjoint")
    #     return y_pred

    def evaluate(self, test, y_test, print_output):
        return evaluate_prediction(
            self.method,
            self.labels,
            y_test,
            self.predict(test),
            print_output=print_output,
        )


class SGD(ML):
    def __init__(self, labels, embedding):
        super(SGD, self).__init__(
            labels=labels,
            classifier=SGDClassifier(penalty="l2", random_state=42),
            parameter={"alpha": (1e-2, 1e-3), "loss": ("hinge", "modified_huber"),},
            embedding=embedding,
        )
        self.method = "sgd"
        if embedding:
            self.method += "_emb"


class NaiveBayes(ML):
    def __init__(self, labels):
        super(NaiveBayes, self).__init__(
            labels=labels, classifier=MultinomialNB(), parameter={}, embedding=False,
        )
        self.method = "naive_bayes"


class AdaBoost(ML):
    def __init__(self, labels, embedding):
        super(AdaBoost, self).__init__(
            labels=labels,
            classifier=AdaBoostClassifier(random_state=42),
            parameter={
                "learning_rate": (0.3, 1.0, 1.7),
                "algorithm": ("SAMME", "SAMME.R"),
            },
            embedding=embedding,
        )
        self.method = "adaboost"
        if embedding:
            self.method += "_emb"


class MLP(ML):
    def __init__(self, labels):
        super(MLP, self).__init__(
            labels=labels,
            classifier=MLPClassifier(random_state=42),
            parameter={
                "activation": ("logistic", "relu"),
                "hidden_layer_sizes": ((50,), (25, 25), (50, 25)),
                "alpha": (0.0001, 0.0003, 0.001),
            },
            embedding=True,
        )
        self.method = "multi_layer_perceptron"
