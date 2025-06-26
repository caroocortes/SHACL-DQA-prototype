from pyshacl import validate
from rdflib import Graph, RDF, RDFS, OWL, Literal, SH, URIRef, Namespace, XSD
import pandas as pd
from collections import defaultdict
import json
import re
from const import *
from collections import Counter
import os
import requests

composite_components = { 
    SH.OrConstraintComponent,
    SH.AndConstraintComponent,
    SH.XoneConstraintComponent,
    SH.NotConstraintComponent
}

# ------------------------------------------------------------------------------------------------------------------- #
#                                       Auxiliary methods
# ------------------------------------------------------------------------------------------------------------------- #

def get_ns(uri):
    if '#' in uri:
        return uri.rsplit('#', 1)[0] + '#'
    else:
        return uri.rsplit('/', 1)[0] + '/'

def get_local_name(uri):
    if '#' in uri:
        return uri.rsplit('#', 1)[-1]
    else:
        return uri.rsplit('/', 1)[-1]

def get_uri_regex_pattern(metadata_file, metadata_format):
    VOID = Namespace("http://rdfs.org/ns/void#")
    g = Graph()
    g.parse(metadata_file, format=metadata_format)
    for dataset in g.subjects(predicate=None, object=VOID.Dataset):
        pattern = g.value(dataset, VOID.uriRegexPattern)
        if pattern:
            return str(pattern)
    return None

# ------------------------------------------------------------------------------------------------------------------- #
#                                       Graph & vocab profile
# ------------------------------------------------------------------------------------------------------------------- #

def profile_graph(dq_assessment, profile_file_path):
    """
    Calculates and stores statistics needed for calculating DQ measures.
    """
    graph = Graph()
    graph.parse(dq_assessment.graph_file_path, format="turtle")

    KNOWN_VOCAB_PREFIXES = (
        "http://www.w3.org/2002/07/owl#",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/2000/01/rdf-schema#",
        "http://rdfs.org/ns/void#",
        "http://www.w3.org/ns/dcat#"
    )

    # number of triples
    num_triples = len(graph)

    # Number of classes (excluding known vocabularies)
    all_classes = set(graph.subjects(RDF.type, OWL.Class)).union(
        set(graph.subjects(RDF.type, RDFS.Class)),
        set(graph.subjects(RDF.type, RDFS.subClassOf)),
        set(graph.objects(None, RDF.type))
    )
    filtered_classes = {c for c in all_classes if not any(str(c).startswith(prefix) for prefix in KNOWN_VOCAB_PREFIXES)}
    num_classes = len(filtered_classes)

    # Number of entities (instances of any class)
    num_entities = len(set(graph.subjects(RDF.type, None)))

    # Number of properties (rdf:Property, owl:ObjectProperty, owl:DatatypeProperty)
    properties = set(graph.subjects(RDF.type, RDF.Property)).union(
        set(graph.subjects(RDF.type, OWL.ObjectProperty)),
        set(graph.subjects(RDF.type, OWL.DatatypeProperty)),
        set(graph.subjects(RDF.type, RDFS.subPropertyOf)),
        set(graph.predicates())
    )
    num_properties = len(properties)

    # Number of triples per property
    triples_per_property = {}
    for p in set(graph.predicates()):
        triples_per_property[str(p)] = len(list(graph.triples((None, p, None))))

    # Number of entities per class
    entities_per_class = {}
    for c in filtered_classes:
        entities_per_class[str(c)] = len(set(graph.subjects(RDF.type, c)))

    # Number of entities with interlinking property
    num_entities_with_interlinking = len(set(graph.subjects(URIRef(dq_assessment.interlinking_property), None)))
    
    # Number of entities with labels
    num_entities_label_property = 0
    if dq_assessment.labeling_property:
        num_entities_label_property = len(set(graph.subjects(URIRef(dq_assessment.labeling_property), None)))

    # Number of entities with descriptions
    num_entities_description_property = 0
    if dq_assessment.description_property:
        num_entities_description_property = len(set(graph.subjects(URIRef(dq_assessment.description_property), None)))

    # Save actual classes and properties as lists of strings
    classes_list = [str(c) for c in filtered_classes]
    properties_list = [str(p) for p in properties]

    profile = {
        "num_triples": num_triples,
        "num_classes": num_classes,
        "num_entities": num_entities,
        "num_properties": num_properties,
        "triples_per_property": triples_per_property,
        "entities_per_class": entities_per_class,
        "num_entities_with_interlinking": num_entities_with_interlinking,
        "num_entities_label_property": num_entities_label_property,
        "num_entities_description_property": num_entities_description_property,
        "classes": classes_list,
        "properties": properties_list
    }

    os.makedirs(PROFILE_DATASETS_FOLDER_PATH, exist_ok=True)
    with open(profile_file_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4)

    return profile


def get_vocab_namespace(graph):
    # Get all subject URIs (corresponds to rdf:about in RDF/XML)
    uris = [str(s) for s in graph.subjects() if isinstance(s, URIRef)]
    if not uris:
        return None
    # Extract namespace for each URI (up to last # or /)
    def get_ns(uri):
        if '#' in uri:
            return uri.rsplit('#', 1)[0] + '#'
        else:
            return uri.rsplit('/', 1)[0] + '/'
    namespaces = [get_ns(uri) for uri in uris]
    if not namespaces:
        return None
    # Return the most common namespace
    ns_counter = Counter(namespaces)
    return ns_counter.most_common(1)[0][0]

def profile_vocab(dq_assessment, vocab):
    """
    Extracts data from a vocabulary.
    """

    vocab_file_name = dq_assessment.config[vocab]["file_path"]
    vocab_name = dq_assessment.config[vocab]["vocab_name"]
    vocab_format = dq_assessment.config[vocab]["file_format"]

    g = Graph()
    g.parse(vocab_file_name, format=vocab_format)

    vocab_ns = get_vocab_namespace(g)

    ontology_info = {
        "classes": [],
        "object_properties": {},
        "datatype_properties": {},
        "deprecated_classes": [],
        "deprecated_properties": [],
        "inverse_functional": [],
        "functional": [],
        "reflexive": [],
        "irreflexive": [],
        "disjoint_classes": set(), 
        "rdf_properties": {},
        "num_classes": 0,
        "num_properties": 0,
        # "num_classes_label": 0,
        # "num_properties_label": 0
    }

    # Classes
    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["classes"].append(str(s))
    for s, p, o in g.triples((None, RDF.type, RDFS.Class)):
        if str(s) not in ontology_info["classes"] and vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["classes"].append(str(s))
    
    # Number of classes
    ontology_info['num_classes'] = len(ontology_info['classes'])

    # # Number of classes with labels
    # classes_with_label = {c for c in ontology_info['classes'] if (c, URIRef(RDFS.label), None) in g}
    # ontology_info['num_classes_label'] = len(classes_with_label)

    # Object Properties + domain/range
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            domain = g.value(s, RDFS.domain)
            range_ = g.value(s, RDFS.range)
            ontology_info["object_properties"][s] = {
                "domain": domain,
                "range": range_
            }
    
    # Number of properties
    ontology_info['num_properties'] += len(ontology_info['object_properties'].keys())

    # Datatype Properties + domain/range
    for s in g.subjects(RDF.type, OWL.DatatypeProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            domain = g.value(s, RDFS.domain)
            range_ = g.value(s, RDFS.range)
            ontology_info["datatype_properties"][s] = {
                "domain": domain,
                "range": range_
            }

    # Number of properties      
    ontology_info['num_properties'] += len(ontology_info['datatype_properties'].keys())

    # Deprecated properties
    for s in g.subjects(OWL.deprecated, Literal(True)):
        if (s, RDF.type, OWL.ObjectProperty) in g or (s, RDF.type, OWL.DatatypeProperty) in g:
            if vocab_ns and str(s).startswith(vocab_ns):
                ontology_info["deprecated_properties"].append(s)

    # Deprecated classes
    for s in g.subjects(OWL.deprecated, Literal(True)):
        if (s, RDF.type, OWL.Class) in g or (s, RDF.type, RDFS.Class) in g:
            if vocab_ns and str(s).startswith(vocab_ns):
                ontology_info["deprecated_classes"].append(s)

    # Inverse functional
    for s in g.subjects(RDF.type, OWL.InverseFunctionalProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["inverse_functional"].append(s)

    # Functional
    for s in g.subjects(RDF.type, OWL.FunctionalProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["functional"].append(s)

    # Irreflexive
    for s in g.subjects(RDF.type, OWL.IrreflexiveProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["irreflexive"].append(s)

    # RDF properties
    dt_props = ontology_info["object_properties"].keys()
    obj_props = ontology_info["datatype_properties"].keys()
    
    for s in g.subjects(RDF.type, RDF.Property):

        if s not in dt_props and s not in obj_props:
            if vocab_ns and str(s).startswith(vocab_ns):
                domain = g.value(s, RDFS.domain)
                range_ = g.value(s, RDFS.range)

                if range_ is not None and (str(range_) == str(RDFS.Literal) or str(range_).startswith(str(XSD))):
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": "literal",
                            "value": range_
                        }
                    }
                elif range_ is not None:   
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": "class",
                            "value": range_
                        }
                    }
    
    # Number of properties      
    ontology_info['num_properties'] += len(ontology_info['rdf_properties'].keys())

    # # Number of properties with labels
    # properties = (
    #     list(ontology_info['rdf_properties'].keys()) +
    #     list(ontology_info['object_properties'].keys()) +
    #     list(ontology_info['datatype_properties'].keys())
    # )
    # properties_with_label = {p for p in properties if (p, URIRef(RDFS.label), None) in g}
    # ontology_info["num_properties_label"] = len(properties_with_label)

    # Disjoint via owl:disjointWith
    disjoint_pairs = set()
    for s, o in g.subject_objects(OWL.disjointWith):
        if vocab_ns and str(s).startswith(vocab_ns) and str(o).startswith(vocab_ns):
            disjoint_pairs.add(frozenset([str(s), str(o)]))

    ontology_info['disjoint_classes'] = [sorted(list(pair)) for pair in disjoint_pairs]

    os.makedirs(PROFILE_VOCABULARIES_FOLDER_PATH, exist_ok=True)
    with open(f'{PROFILE_VOCABULARIES_FOLDER_PATH}/{vocab_name}.json', "w", encoding="utf-8") as f:
        json.dump(ontology_info, f, indent=4)

    return vocab_ns

# ------------------------------------------------------------------------------------------------------------------- #
#                                       SHACL validation
# ------------------------------------------------------------------------------------------------------------------- #

def create_shape_graph(shacl_shapes):
    """
    Creates shape graph.
    """
    prefixes = """
        @prefix sh: <http://www.w3.org/ns/shacl#> . \n
        @prefix ex: <https://www.example.org#> . \n
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> . \n
        @prefix void: <http://rdfs.org/ns/void#> . \n
        @prefix owl: <http://www.w3.org/2002/07/owl#> . \n
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>. \n
        @prefix dcterms: <http://purl.org/dc/terms/> . \n
        @prefix foaf: <http://xmlns.com/foaf/0.1/> . \n
        @prefix dcat: <http://www.w3.org/ns/dcat#> .
    """

    data = prefixes + '\n' + shacl_shapes

    shapes_graph = Graph()
    shapes_graph.parse(data=data, format="ttl")

    return shapes_graph

def validate_shacl_constraints(data_graph_file_path, data_graph_file_format, shapes_graph, inference):
    """
    Calculates and stores statistics needed for calculating DQ measures.
    """
    data_graph = Graph().parse(data_graph_file_path, format=data_graph_file_format)

    if inference:
        results = validate(
            data_graph,
            shacl_graph=shapes_graph,
            debug=False,
            inference='both'
        )
    else:
        results = validate(
            data_graph,
            shacl_graph=shapes_graph,
            debug=False
        )

    conforms, report_graph, validation_report = results

    return conforms, report_graph, validation_report

def get_metric_message(results_graph, result):
    constraint_type = results_graph.value(result, SH.sourceConstraintComponent)
    counter = -1
    # Composite constraints don't output individual validation results for each constraint inside the composite
    # They just output that the node must conform to one or more shapes in the **composite_shape**
    # Therefore, the sh:message with the name of the metric is in the resultMessage
    if constraint_type in composite_components:
        metric = results_graph.value(result, SH.sourceShape).removesuffix("Shape").removeprefix("https://www.example.org#")
        result_message = results_graph.value(result, SH.resultMessage)
        
        pattern_message = r'sh:message\s+Literal\("([^"]+)"\)'
        message = ''
        match = re.search(pattern_message, result_message)
        if match:
            message = match.group(1)
    else:
        message = str(results_graph.value(result, SH.resultMessage))

        if "_" in message: 
            # To handle shapes for a specific property/class
            # shape message: Metric_Counter - Message

            # Get Metric and Counter - Message separately
            metric, counter_message = [part.strip() for part in message.split("_", 1)]

            # Get Counter and Message separately
            counter, message = [part.strip() for part in counter_message.split("-", 1)]
            
        else:
            # Remaining shapes: Metric - Message
            metric_message = message.split("-")
            metric = metric_message[0].strip()
            message = metric_message[1].strip() 

            if 'URIsLengthAndParameters' in metric:
                # this shapes has 2 different constraints
                # if constraints_type is SH.NotConstraintComponent the shape checks for URIs parameters
                # if constraints_type is SH.MaxLengthConstraintComponent the shape checks for URIs length
                message = 'URIs should not contain parameters' if constraint_type == SH.NotConstraintComponent else 'URIs are too long'  

    return metric, message, counter

def get_denominator(metric, info, dataset_profile):
    """
    Get denominator for the metric.
    """
    metric_prefix = metric.split('_')[0] if '_' in metric else metric
    if metric_prefix in NUM_ENTITIES:
        if metric == 'DifferentLanguagesLabelsEntities':
            return dataset_profile.get("num_entities_label_property", 1)
        elif metric == 'DifferentLanguagesDescriptionsEntities':
            return dataset_profile.get("num_entities_description_property", 1)
        else:
            return dataset_profile.get("num_entities", 1)
    elif metric_prefix in NUM_CLASSES:
        return dataset_profile.get("num_classes", 1)
    elif metric_prefix in NUM_PROPERTIES:
        return dataset_profile.get("num_properties", 1)        
    elif metric_prefix in NUM_TRIPLES_PER_PROPERTY:
        if "property" in info:
            return dataset_profile.get("triples_per_property", {}).get(info['property'], 1)
    elif metric_prefix in NUM_ENTITIES_PER_CLASS:  
        if "class" in info:
            return dataset_profile.get("entities_per_class", {}).get(info['class'], 1)

