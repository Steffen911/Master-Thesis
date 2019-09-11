import json
from datetime import datetime as dt

with open("../../Data/clusters.csv", "w") as f:
    print('"id"\t"size"\t"category"', file=f)

# Extract the data from WDC gold standard corpus
with open("../Data/idclusters.json", mode="r") as f:
    i = 0
    inserted = 0
    for line in iter(f.readline, ""):
        if i % 500000 == 0:
            print(
                "{}: processed {}/10 million lines so far".format(dt.now(), i / 1000000)
            )
        i += 1
        parsed = json.loads(line)
        with open("../../Data/clusters.csv", "a") as o:
            inserted += 1
            print(
                '"{}"\t"{}"\t"{}"'.format(
                    parsed["id"], parsed["size"], parsed["category"]
                ),
                file=o,
            )

    print("completed processing. inserted {} lines".format(inserted))
