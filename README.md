# Master Thesis

This repository contains the source for my [Master Thesis](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Master_Thesis_Steffen_Schmitz.pdf)
"Product Taxonomy Matching in E-Commerce Environments".
It was handed in on May 3rd, 2020 at the University of Mannheim.

## Repository Layout

`Thesis` contains the LaTeX code to produce the written Thesis that was handed in at the Data and Web Science group
at the University of Mannheim.
You can use the `build.sh` script to compile the Thesis and output a `thesis.pdf`.
It should work with any standard TeX distribution.

`Code` contains the source code to reproduce the experiments in this Thesis.

## Requirements

- Python 3.x
- Maven 3.x
- Java 1.8 or later

## Quick Start

```
mkdir -p Data
wget https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/products.json -O Data/products.json
wget https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/training.csv -O Data/training.csv
wget https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/goldstandard_positive.csv -O Data/goldstandard_positive.csv
pipenv install
pipenv shell
cd Code
python main.py
```

## Code Documentation

The layout of the  Code directory is as follows:
```
Code
├── crawler
├── main.py
├── matchers
├── thesis
└── wdc
```

 `main.py` runs all sub-components at once.
 First, it creates pairs from the crawled datasets and creates a labelled training set from them.
 Then it runs the experiments on the manually annotated goldstandard.
 
 The individual methods that are used from `main.py` are in the `thesis` package.
 There are methods to create the training set and run the experiments.
 It also contains a package to create statistics about the training set.
 To get running, simply download the following files and put it into a `Data` directory on the project root.
 
 - [clothing_products.json](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/clothing_products.json)
 - [electronic_products.json](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/electronic_products.csv)
 - [products.json](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/products.json)
 - [training.csv](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/training.csv) (Generated labels)
 - [goldstandard_positive.csv](https://steffen911-papers.s3.eu-central-1.amazonaws.com/Data/goldstandard_positive.csv) (Manually verified positive examples) 
 
 Afterwards run `main.py` and everything should run out of the box.
 All code expects to be executed from the `Code` directory.
 
 In `thesis/experiments.py` different matchers are used on the goldstandard and training set.
 All matcher implementations are in the `matchers` package, except for S-Match were we reused the open source
 implementation provided by the authors.
 The source code can be found on [GitHub](https://github.com/opendatatrentino/s-match).
 We also provide an updated version in this repository that fixes minor bugs.
 
 The `crawler` package contains code to retrieve data from the PLDs we covered and `wdc` contains code to extract
 the categories from the WDC Product Corpus and combine them with the WDC training dataset for product matching.
