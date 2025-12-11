## Overview

This is a small project that recommends alternative products when the requested one is out of stock. Everything runs on a simple knowledge graph instead of machine learning. Products, categories and tags are stored as nodes, and relationships between them are edges. The program uses BFS, rule-based filtering and scoring to pick substitutes. A Streamlit UI is included so it can run like a small tool.

## How it works

The knowledge graph is built from a CSV file.
Each product has:

* an id
* category
* brand
* price
* stock status
* tags like lactose_free, veg, vegan, wholegrain

These are turned into nodes.
Edges connect products to their category and to their tags.

Example:

* amul_milk_1l → milk (IS A)
* amul_milk_1l → veg (HAS TAG)

Once the graph is built, the program uses BFS starting from the requested product. This lets it naturally discover similar or related products by moving through categories and tags.

After BFS, the list of products is filtered using basic rules:

* must be in stock
* must be below or equal to the max price given
* must contain all required tags
* optional brand preference

Next, scoring is applied. The scoring is simple:

* same category: +3
* similar category (category connected through one hop): +1
* same brand: +1
* cheaper than the requested product: +1

Finally, rule explanations are created so the user knows why each recommendation was chosen. These are just tags like:

* same_category
* similar_category
* all_required_tags_matched
* cheaper_option
* same_brand or different_brand

The top three highest scoring products are shown.

## Streamlit app

The UI lets the user:

* pick the product they wanted
* set a max price
* type required tags
* add an optional preferred brand
* get the recommended substitutes

Everything is displayed cleanly with the rules and scores.

To run the UI:

```
pip install streamlit networkx matplotlib
streamlit run graph.py
```

Make sure `products.csv` is in the same folder.

## Files

* `graph.py` – entire program (graph builder, BFS, scoring, rules, Streamlit UI)
* `products.csv` – sample dataset for the knowledge graph

## CSV format

The CSV should have these columns:

```
id,category,brand,price,stock,tags
```

Example:

```
amul_milk_1l,milk,Amul,60,false,veg;lactose
mother_dairy_milk_1l,milk,MotherDairy,55,true,veg;lactose
sofit_soy_milk,plant_milk,Sofit,90,true,veg;lactose_free;vegan
```

