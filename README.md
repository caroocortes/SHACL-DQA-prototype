# SHACL-based Data Quality Assessment prototype

This project provides a SHACL-based prototype to assess and visualize data quality measures over RDF datasets.

---

## Example
A toy example based on the *pizza.owl* ontology is included in the repository. Note that the ontology was modified to trigger violations.
Run the example with ``python3 main.py -d pizza -ra`` or just visualize the results with ``streamlit run visualize_results.py``.

---
## Setup Instructions

**Python version:** 3.13.2

### 1. Create and activate a virtual environment 
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download the datasets 
Download the datasets & metadata files (VoID descriptions) from [https://zenodo.org/records/16644385]
Datasets:
- *temples_data.ttl* & *temples_void.ttl*
- *dbtunes_data.ttl* & *dbtunes_void.ttl*
- *drugbank_data.nt* & *drugbank_void.ttl*

Store the datasets & metadata files in the folder ``datasets/temples_classical_world/``, ``datasets/drugbank/``, and ``datasets/dbtunes_john_peel_sessions/``, respectively.

### 3. Run assessment
In root of the project run: ``python3 main.py -d dataset_name -ra [-rd -rm -rv]``
- *-d* can be temples, drugbank, dbtunes (the name of the config file)
- *-ra*: Runs the complete assessment on data, metadata, and vocabularies.
- *-rd*, *-rm*, *-rv*: Allow you to selectively run parts of the assessment. You can use one or more of these flags together, unless -ra is specified.

Inside each dataset folder, the ``results/`` subfolder contains the DQA results, and the ``shapes/`` subfolder contains the instantiated shapes used for the assessment.

*Execution time per dataset (Macbook Pro, 16GB):*
- temples: 40 secs approx.
- drugbank: 3 hours approx.
- dbtunes: 20 minutes approx.

### 4. Run streamlit dashboard
In root of the project run: ``streamlit run visualize_results.py``

## Project structure
```
.
├── config/                   # Dataset's config files - see config_template.ini for the config template
├── datasets/
│   ├── dataset_1/            # Datasets
│       |── results           # DQA results
│       |── shapes            # Shapes used for DQA
│       dataset_1.ttl         # Dataset file
│       void.ttl              # Metadata file
│   └── dataset_2/          
│       ...
|   |-- vocabularies/         # Datasets' vocabularies
├── dq_assessment/            # DQA results
    |── metrics_template      # DQ metrics templates (info. about the implemented metrics)                  
    |── shapes                # Shapes templates
├── profile/                  # Stores profiles of the data & vocabularies/ontologies
|   ├── datasets/
|   ├── vocabularies/
├── main.py                   # Runs DQA
├── dq_assessment.py          # Class in charge of DQA
├── visualize_results.py      # Class in charge of running the streamlit dashboard
├── shacl_shape_builder.py    # Class in charge of instantiating the shapes templates
├── requirements.txt   
└── README.md             
```