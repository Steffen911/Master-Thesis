import findspark
import re
from urllib.parse import urlparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType


def is_unequal(row):
    return (
        row.nodeID_l != row.nodeID_r
        and row.url_l != row.url_r
        and row.pld_l != row.pld_r
    )


def run(data_dir):
    findspark.init()
    spark = (
        SparkSession.builder.appName("thesis")
        .master("local[4]")
        .config("spark.executor.memory", "8G")
        .config("spark.driver.memory", "8G")
        .config("spark.driver.maxResultSize", "8G")
        .getOrCreate()
    )

    p = (
        spark.read.option("header", "true")
        .option("delimiter", "\t")
        .csv(f"{data_dir}/products.csv")
        .cache()
    )
    t = (
        spark.read.option("header", "true")
        .option("delimiter", "\t")
        .csv(f"{data_dir}/taxonomies.csv")
        .cache()
    )
    c = (
        spark.read.option("header", "true")
        .option("delimiter", "\t")
        .csv(f"{data_dir}/clusters.csv")
        .cache()
    )

    cond = [p.parent_NodeID == t.subject, p.url == t.provenance]
    parents = p.join(t, cond, "inner").select(
        p.nodeID,
        p.cluster_id,
        p.url,
        t.predicate.alias("type"),
        t.object.alias("taxonomy"),
    )

    cond = [p.nodeID == t.subject, p.url == t.provenance]
    products = p.join(t, cond, "inner").select(
        p.nodeID,
        p.cluster_id,
        p.url,
        t.predicate.alias("type"),
        t.object.alias("taxonomy"),
    )

    df = parents.unionAll(products).dropDuplicates()

    # get the PLD
    parse_netloc = udf(lambda x: urlparse(x).netloc, StringType())
    df = df.withColumn("domain", parse_netloc(df.url))

    # store the actual pld
    # remove domain extension and use last element as PLD
    # e.g. foo.com becomes test and foo.bar.com becomes bar
    # => m.foo.com and en.foo.com are treated as the same PLD
    english_domains = re.compile("\.com$|\.net$|\.org$|\.co\.uk|\.us", re.IGNORECASE)
    get_pld = udf(lambda x: english_domains.sub("", x).split(".")[-1], StringType())
    df = df.withColumn("pld", get_pld(df.domain))

    # get only products which are in the Clothing or Computers_and_Accessories cluster
    c = c.filter(
        (c.category == "Clothing")
        | (c.category == "Computers_and_Accessories")
        | (c.category == "Cell_Phones_and_Accessories")
        | (c.category == "Camera_and_Photo")
        | (c.category == "Other_Electronics")
        | (c.category == "Shoes")
        | (c.category == "Sports_and_Outdoors")  # |
        # (c.category == "Custom_Crawl")
    ).cache()
    df = df.join(c, df.cluster_id == c.id, "left_semi").cache()
    print(df.count())

    df = df.toPandas()

    joined = df.join(
        df.set_index("cluster_id"),
        on="cluster_id",
        how="inner",
        lsuffix="_l",
        rsuffix="_r",
    )
    print("joined dataframe on cluster id")
    joined = joined[joined.apply(is_unequal, axis=1)]
    print("filtered unnecessary self join tuples")
    joined.to_csv(f"{data_dir}/joined.csv", sep="\t")
    print(joined.count())


if __name__ == "__main__":
    run("../../Data")
