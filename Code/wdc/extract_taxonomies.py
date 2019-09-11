import gc
import re
import gzip
from urllib.parse import urlparse
from datetime import datetime as dt

taxo_pattern = re.compile(
    "<http://schema.org/Product/category>|<http://schema.org/Product/breadcrumb>|<http://data-vocabulary.org/Breadcrumb/title|<http://schema.org/WebPage/breadcrumb>|<http://schema.org/ListItem|<http://schema.org/BreadcrumbList|<http://schema.org/Product>",
    re.IGNORECASE,
)
split_pattern = re.compile("^(_:.*)\s<(.*?)>\s(.*)\s<(.*)>\s\.$", re.IGNORECASE)
english_domains = re.compile("\.com$|\.net$|\.org$|\.co\.uk|\.us", re.IGNORECASE)
tax_cleaner = re.compile(r"'|\\n|\\t|@[a-z][a-z](-[A-Z][A-Z])?")
white_space = re.compile("\s+")


def insert_breadcrumbs(products, breadcrumblists, itemlistelements, listitemprops):
    inserted = 0
    bcl_size = len(breadcrumblists)
    for idx, bc in enumerate(breadcrumblists):  # breadcrumb
        if idx % 10000 == 0:
            print(
                "{}: \tprocessed {}/{} breadcrumblists so far".format(
                    dt.now(), idx, bcl_size
                )
            )

        breadcrumb = []
        ile = itemlistelements.get(bc, [])  # itemlistelements
        for le in ile:
            lip = listitemprops.get((le, bc[1]), [])  # listitemproperty
            for p in lip:
                if p[0].lower() == "http://schema.org/ListItem/name".lower():
                    cleaned = white_space.sub(" ", tax_cleaner.sub("", p[1]).strip())
                    breadcrumb.append(cleaned)

        if len(breadcrumb) > 0:
            with open("../../Data/taxonomies.csv", "a") as o:
                inserted += 1
                print(
                    '"{}"\t"{}"\t"{}"\t"{}"'.format(
                        products.get(bc[1], ""),
                        "http://schema.org/BreadcrumbList",
                        " > ".join(breadcrumb),
                        bc[1],
                    ),
                    file=o,
                )

    print("{}: \tinserted {} breadcrumblist entries".format(dt.now(), inserted))


with open("../../Data/taxonomies.csv", "w") as f:
    print('"subject"\t"predicate"\t"object"\t"provenance"', file=f)

with gzip.open("../Data/schema_Product.gz", "rt") as f:
    i = 0
    inserted = 0

    products = {}
    breadcrumblists = []
    listitems = []
    itemlistelements = {}
    listitemprops = {}

    for line in iter(f.readline, ""):
        if i % 5000000 == 0:
            print(
                "{}: processed {}/6321 million lines so far".format(
                    dt.now(), i / 1000000
                )
            )
        i += 1

        if i % 100000000 == 0:
            print("{}: persisting the current breadcrumbs".format(dt.now()))
            insert_breadcrumbs(
                products, breadcrumblists, itemlistelements, listitemprops
            )
            products = {}
            breadcrumblists = []
            listitems = []
            itemlistelements = {}
            listitemprops = {}
            gc.collect()

        if not taxo_pattern.search(line):
            continue
        line = line.replace('"', "'")
        match = split_pattern.match(line)
        if match is None:
            continue
        props = match.groups()
        if len(props) != 4:
            print("properties have weird length: " + str(props))
            continue
        pld = urlparse(props[3]).netloc
        if not bool(english_domains.search(pld)):
            # skip domain endings that are not english
            continue

        if props[2].lower() == "<http://schema.org/BreadcrumbList>".lower():
            breadcrumblists.append((props[0], props[3]))
            continue
        if props[2].lower() == "<http://schema.org/ListItem>".lower():
            listitems.append((props[0], props[3]))
            continue
        if (
            props[1].lower()
            == "http://schema.org/BreadcrumbList/itemListElement".lower()
        ):
            pos = (props[0], props[3])
            itemlistelements[pos] = itemlistelements.get(pos, []) + [props[2]]
            continue
        if (
            "http://schema.org/ListItem".lower() in props[1].lower()
            or "http://schema.org/BreadcrumbList".lower() in props[1].lower()
        ):
            pos = (props[0], props[3])
            listitemprops[pos] = listitemprops.get(pos, []) + [(props[1], props[2])]
            continue
        if props[2].lower() == "<http://schema.org/Product>".lower():
            products[props[3]] = props[0]
            continue

        with open("../../Data/taxonomies.csv", "a") as o:
            inserted += 1
            cleaned = white_space.sub(" ", tax_cleaner.sub("", props[2]).strip())
            print(
                '"{}"\t"{}"\t"{}"\t"{}"'.format(props[0], props[1], cleaned, props[3]),
                file=o,
            )

    insert_breadcrumbs(products, breadcrumblists, itemlistelements, listitemprops)

print("{}: inserted {} lines".format(dt.now(), inserted))
