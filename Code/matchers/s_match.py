import re
from matchers.matcher import Matcher
from thesis.evaluation import evaluate_prediction


def find_prediction(row):
    fn = "../Data/result.txt"
    left = re.escape("\\Top\\" + row.taxonomy_l.replace(" > ", "\\"))
    right = re.escape("\\Top\\" + row.taxonomy_r.replace(" > ", "\\"))
    with open(fn, "r") as f:
        for line in f.readlines():
            pattern = re.compile(left + r"\t(.*)\t" + right)
            m = pattern.search(line)
            if m is not None:
                pred = m.group(1)
                if pred == "=":
                    return "equal"
                if pred == ">":
                    return "contains"
                if pred == "<":
                    return "contained-in"
                if pred == "!":
                    return "disjoint"
                else:
                    raise Exception("Unknown predicate")
    return "disjoint"


class SMatch(Matcher):
    def __init__(self, labels):
        super(SMatch, self).__init__(labels)
        self.method = "s_match"

    def predict(self, test):
        # fake prediction by loading results from Data
        return test.apply(find_prediction, axis=1)

    def evaluate(self, test, y_test, print_output=False):
        return evaluate_prediction(
            self.method,
            self.labels,
            y_test,
            self.predict(test),
            print_output=print_output,
        )
