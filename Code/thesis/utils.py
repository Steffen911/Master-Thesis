import re
import numpy as np
from scipy import spatial
import gensim.downloader as api

alphanum = re.compile(r"[\W_]+")
model = api.load("word2vec-google-news-300")
embedding_dim = 300


def split_composite(w):
    m = re.split(r", | & | and |\s", w)
    return set([alphanum.sub("", s.lower()) for s in m])


def _get_embedding(label_set):
    result = [0] * embedding_dim
    num_words = len(label_set)
    for label in label_set:
        try:
            result += model[label]
        except KeyError:
            num_words -= 1
    if num_words == 0:
        return [0] * embedding_dim
    return np.array(result) / num_words


def get_class_vector(class_hier):
    f"""
    get_class_vector takes a string class label and returns a {embedding_dim} dimensional vector.
    The hierarchy levels are weighted with the lowest level getting the highest weight.
    :param class_hier: Class-label with a schema like "Top > Lower > Bottom"
    :return: {embedding_dim}-dimensional vector representing the class-label
    """
    *remain, last = class_hier.split(" > ")
    if last == "":
        return [0] * embedding_dim
    return 0.7 * np.array(_get_embedding(split_composite(last))) + 0.3 * np.array(
        get_class_vector(" > ".join(remain))
    )


def embedding_cosine_sim(class_l, class_r):
    """
    embedding_cosine_sim takes to string class labels, encodes them, and returns
    the cosine similarity.
    :param class_l: Class-label with a schema like "Top > Lower > Bottom"
    :param class_r: Class-label with a schema like "Top > Lower > Bottom"
    :return: cosine similarity between two class-labels
    """
    vector_l = get_class_vector(class_l)
    vector_r = get_class_vector(class_r)
    return 1 - spatial.distance.cosine(vector_l, vector_r)


if __name__ == "__main__":
    res = get_class_vector("Clothing, Shoes & Jewelry > Women > Watches > Smartwatches")
    print(res)
