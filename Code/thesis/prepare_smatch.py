import subprocess
from thesis.experiments import tuples, get_goldstandard

taxo_l = dict()
taxo_r = dict()


def fill_taxo(taxo, hier):
    splitted = hier.split(" > ")
    for index, label in enumerate(splitted):
        if index == 0:
            taxo[label] = taxo.get(label, dict())
        if index == 1:
            taxo[splitted[0]][label] = taxo[splitted[0]].get(label, dict())
        if index == 2:
            taxo[splitted[0]][splitted[1]][label] = taxo[splitted[0]][splitted[1]].get(
                label, dict()
            )
        if index == 3:
            taxo[splitted[0]][splitted[1]][splitted[2]][label] = taxo[splitted[0]][
                splitted[1]
            ][splitted[2]].get(label, dict())
        if index == 4:
            taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][label] = taxo[
                splitted[0]
            ][splitted[1]][splitted[2]][splitted[3]].get(label, dict())
        if index == 5:
            taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][splitted[4]][
                label
            ] = taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][
                splitted[4]
            ].get(
                label, dict()
            )
        if index == 6:
            taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][splitted[4]][
                splitted[5]
            ][label] = taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][
                splitted[4]
            ][
                splitted[5]
            ].get(
                label, dict()
            )
        if index == 7:
            taxo[splitted[0]][splitted[1]][splitted[2]][splitted[3]][splitted[4]][
                splitted[5]
            ][splitted[6]][label] = taxo[splitted[0]][splitted[1]][splitted[2]][
                splitted[3]
            ][
                splitted[4]
            ][
                splitted[5]
            ][
                splitted[6]
            ].get(
                label, dict()
            )


def print_dict_tree(f, dictionary, indent):
    for key in dictionary:
        tabs = "\t".join([""] * (indent + 1))
        print(f"{tabs}{key}", file=f)
        print_dict_tree(f, dictionary[key], indent + 1)


def run(data_dir):
    gs = get_goldstandard(data_dir)

    cond = list(
        map(
            lambda x: f"((gs['pld_l'] == '{x[0]}') & (gs['pld_r'] == '{x[1]}'))", tuples
        )
    )
    gs = gs[eval(f"({' | '.join(cond)})")]

    for hier in gs.taxonomy_l:
        fill_taxo(taxo_l, hier)

    for hier in gs.taxonomy_r:
        fill_taxo(taxo_r, hier)

    with open(f"{data_dir}/taxo_l.txt", "w") as f:
        print_dict_tree(f, taxo_l, 0)
    with open(f"{data_dir}/taxo_r.txt", "w") as f:
        print_dict_tree(f, taxo_r, 0)

    subprocess.call(["./s-match/run.sh"])


if __name__ == "__main__":
    run("../Data")
