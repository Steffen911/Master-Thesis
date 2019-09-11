import pandas as pd


class Matcher:
    def __init__(self, labels):
        self.labels = labels
        self.method = ""

    def train(self, train, y_train):
        raise NotImplementedError("subclasses should implement train")

    def predict(self, test):
        raise NotImplementedError("subclasses should implement predict")

    def evaluate(self, test, y_test, print_output):
        raise NotImplementedError("subclass should implement evaluate")

    def print_prediction(self, data_dir, test):
        res = test[["taxonomy_l", "taxonomy_r", "label"]]
        res.reset_index(drop=True, inplace=True)
        y_pred = pd.Series(self.predict(test)).to_frame().reset_index(drop=True)
        res = pd.concat([res, y_pred], axis=1, ignore_index=True)
        res.columns = ["taxonomy_l", "taxonomy_r", "y_true", "y_pred"]
        res.to_csv(f"{data_dir}/predictions_{self.method}.csv", mode="a", header=False)
