import logging
from thesis.crawl import run as crawl
from thesis.create_pairs import create_pairs
from thesis.statistics import run as prepare_statistics
from thesis.experiments import run as run_experiments
from thesis.goldstandard import run as create_goldstandard
from thesis.prepare_smatch import run as prepare_smatch

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s %(message)s", level=logging.INFO
)


def run(data_dir):
    # fetch categories from products
    # crawl(data_dir)

    # pair all products together
    # create_pairs(data_dir)

    # create a training dataset from the product information
    # create_goldstandard(data_dir)

    # prepare files for s-match and run all experiments
    prepare_smatch(data_dir)
    run_experiments(data_dir)

    # create statistics about the trainingset and goldstandard
    prepare_statistics(data_dir)


if __name__ == "__main__":
    run("../Data")
