import json
from datetime import datetime as dt

with open("../../Data/products.csv", "w") as f:
    print('"nodeID"\t"url"\t"cluster_id"\t"parent_NodeID"\t"relationToParent"', file=f)

# Extract the data from WDC gold standard corpus
with open("../Data/offers_english.json", mode="r") as f:
    i = 0
    inserted = 0
    for line in iter(f.readline, ""):
        if i % 500000 == 0:
            print(
                "{}: processed {}/16 million lines so far".format(dt.now(), i / 1000000)
            )
        i += 1
        parsed = json.loads(line)
        with open("../../Data/products.csv", "a") as o:
            inserted += 1
            print(
                '"{}"\t"{}"\t"{}"\t"{}"\t"{}"'.format(
                    parsed["nodeID"],
                    parsed["url"],
                    parsed["cluster_id"],
                    parsed["parent_NodeID"],
                    parsed["relationToParent"],
                ),
                file=o,
            )

    print("completed processing. inserted {} lines".format(inserted))
