from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def _remove_last(x):
    splitted = x.split(">")
    if len(splitted) == 0 or len(splitted) == 1:
        return x
    return ">".join(splitted[0:-1])


def _set_label(x, t):
    if max(x) < t:
        return "disjoint"
    try:
        ind = x.to_list().index(max(x))
    except:
        return "disjoint"
    if ind == 0:
        return "equal"
    # enable for n-gram experiment
    # if x[1] == x[2]:
    #     return "disjoint"
    if ind == 1:
        return "contained-in"
    if ind == 2:
        return "contains"


def get_aggregate_evaluation(labels, eval_result):
    """
    get_aggregate_evaluation returns the average F1 score across the given labels.
    :param labels: Labels used for the prediction.
    :param eval_result: Result object
    :return: Average F1 score
    """
    score = 0
    for label in labels:
        score += eval_result[label]["f1"]
    return score / len(labels)


def evaluate_prediction(method, labels, lbl, pred, print_output=False):
    """
    evaluate_prediction compares the predicted labels with the expected labels and returns
    the evaluation result.
    :param method: String label to identify the evaluated method
    :param labels: Labels used for the prediction
    :param lbl: Expected labels
    :param pred: Predicted labels
    :param print_output: Print intermediate results
    :return: {<label>: {precision, recall, f1}, confusion_matrix}
    """
    if print_output:
        print(f"evaluating {method}...")

    results = {}
    for label in labels:
        precision, recall, f1, support = precision_recall_fscore_support(
            lbl, pred, labels=[label], average="macro"
        )
        if print_output:
            print(f"{label} -> precision: {precision}, recall: {recall}, f1: {f1}")
        results[label] = {"precision": precision, "recall": recall, "f1": f1}

    results["confusion_matrix"] = confusion_matrix(
        lbl, pred, labels=["equal", "contains", "contained-in", "disjoint"]
    )

    if print_output:
        print(f"confusion matrix for {method}:")
        print(results["confusion_matrix"])

    return results
