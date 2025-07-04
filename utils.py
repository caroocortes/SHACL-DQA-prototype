from pyshacl import validate
from rdflib import Graph, RDF, RDFS, OWL, Literal, SH, URIRef, Namespace, XSD
import json
import re
from const import *
from collections import Counter
import os

composite_components = { 
    SH.OrConstraintComponent,
    SH.AndConstraintComponent,
    SH.XoneConstraintComponent,
    SH.NotConstraintComponent
}

# ------------------------------------------------------------------------------------------------------------------- #
#                                       Auxiliary methods
# ------------------------------------------------------------------------------------------------------------------- #

def escape_dots_for_turtle_regex(s):
    return s.replace("\\", "\\\\")

def python_regex_to_shacl_regex(python_regex):
    # Convert to a Turtle-ready regex string by doubling backslashes
    return python_regex.replace('\\', '\\\\')

def get_ns(uri):
    if '#' in uri:
        return uri.rsplit('#', 1)[0] + '#'
    else:
        return uri.rsplit('/', 1)[0] + '/'

def get_uri_regex_pattern(metadata_file, metadata_format):
    VOID = Namespace("http://rdfs.org/ns/void#")
    g = Graph()
    g.parse(metadata_file, format=metadata_format)
    for dataset in g.subjects(predicate=None, object=VOID.Dataset):
        pattern = g.value(dataset, VOID.uriRegexPattern)
        if pattern:
            return str(pattern)
    return None

def get_uri_space(metadata_file, metadata_format):
    VOID = Namespace("http://rdfs.org/ns/void#")
    g = Graph()
    g.parse(metadata_file, format=metadata_format)
    for dataset in g.subjects(predicate=None, object=VOID.Dataset):
        pattern = g.value(dataset, VOID.uriSpace)
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

    # number of triples
    num_triples = len(graph)

    # Number of classes 
    all_classes = set(graph.objects(None, RDF.type))
    num_classes = len(all_classes)

    # Number of entities (instances of any class)
    num_entities = len(set(graph.subjects(RDF.type, None)))

    # Number of properties used -> predicate position of triples
    properties = set(graph.predicates())
    num_properties = len(properties)

    # Number of triples per property
    triples_per_property = {}
    for p in set(graph.predicates()):
        triples_per_property[str(p)] = len(list(graph.triples((None, p, None))))

    # Number of unique subjects that use a property
    subjects_per_property = {}
    for p in set(graph.predicates()):
        subjects = set(s for s, _, _ in graph.triples((None, p, None)))
        subjects_per_property[str(p)] = len(subjects)

    # Number of entities per class
    entities_per_class = {}
    for c in all_classes:
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
    classes_list = [str(c) for c in all_classes]
    properties_list = [str(p) for p in properties]

    profile = {
        "num_triples": num_triples,
        "num_classes": num_classes,
        "num_entities": num_entities,
        "num_properties": num_properties,
        "subjects_per_property": subjects_per_property,
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
        "transitive": [],
        "asymmetric": [],
        "symmetric": [],
        "disjoint_classes": set(), 
        "rdf_properties": {},
        "num_classes": 0,
        "num_properties": 0,
        "num_all_classes": 0,
        "num_all_properties": 0
    }

    # Classes
    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        if vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(OWL.deprecated, Literal(True)) and not s in g.subjects(RDF.type, OWL.DeprecatedClass):
            ontology_info["classes"].append(str(s))
    for s, p, o in g.triples((None, RDF.type, RDFS.Class)):
        if str(s) not in ontology_info["classes"] and vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(RDF.type, OWL.DeprecatedClass):
            ontology_info["classes"].append(str(s))
    
    # Number of classes
    ontology_info['num_classes'] = len(ontology_info['classes'])

    # # Number of classes with labels
    # classes_with_label = {c for c in ontology_info['classes'] if (c, URIRef(RDFS.label), None) in g}
    # ontology_info['num_classes_label'] = len(classes_with_label)

    # Object Properties + domain/range
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        if vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(OWL.deprecated, Literal(True)) and not s in g.subjects(RDF.type, OWL.DeprecatedProperty):
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
        if vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(OWL.deprecated, Literal(True)) and not s in g.subjects(RDF.type, OWL.DeprecatedProperty):
            domain = g.value(s, RDFS.domain)
            range_ = g.value(s, RDFS.range)
            ontology_info["datatype_properties"][s] = {
                "domain": domain,
                "range": range_
            }

    # Number of properties      
    ontology_info['num_properties'] += len(ontology_info['datatype_properties'].keys())

    dt_props = ontology_info["object_properties"].keys()
    obj_props = ontology_info["datatype_properties"].keys()

    # Deprecated properties
    for s in g.subjects(OWL.deprecated, Literal(True)):
        if (s, RDF.type, OWL.ObjectProperty) in g or (s, RDF.type, OWL.DatatypeProperty) in g:
            if vocab_ns and str(s).startswith(vocab_ns):
                ontology_info["deprecated_properties"].append(s)
    
    for s in g.subjects(RDF.type, OWL.DeprecatedProperty):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["deprecated_properties"].append(s)

    # Deprecated classes
    for s in g.subjects(OWL.deprecated, Literal(True)):
        if (s, RDF.type, OWL.Class) in g or (s, RDF.type, RDFS.Class) in g:
            if vocab_ns and str(s).startswith(vocab_ns):
                ontology_info["deprecated_classes"].append(s)

    for s in g.subjects(RDF.type, OWL.DeprecatedClass):
        if vocab_ns and str(s).startswith(vocab_ns):
            ontology_info["deprecated_classes"].append(s)

    # Inverse functional
    for s in g.subjects(RDF.type, OWL.InverseFunctionalProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):

            ontology_info["inverse_functional"].append(s)

            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # Functional
    for s in g.subjects(RDF.type, OWL.FunctionalProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):
            
            ontology_info["functional"].append(s)
            
            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # Irreflexive
    for s in g.subjects(RDF.type, OWL.IrreflexiveProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):
            
            ontology_info["irreflexive"].append(s)

            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

   # Reflexive 
    for s in g.subjects(RDF.type, OWL.IrreflexiveProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):
            
            ontology_info["reflexive"].append(s)

            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # Symmetric
    for s in g.subjects(RDF.type, OWL.SymmetricProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):

            ontology_info["symmetric"].append(s)
            
            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # Asymmetric
    for s in g.subjects(RDF.type, OWL.AsymmetricProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty) ):
            
            ontology_info["asymmetric"].append(s)

            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # Transitive
    for s in g.subjects(RDF.type, OWL.TransitiveProperty):
        if (vocab_ns and str(s).startswith(vocab_ns) and 
            s not in g.subjects(OWL.deprecated, Literal(True)) and 
            s not in g.subjects(RDF.type, OWL.DeprecatedProperty)):
            
            ontology_info["transitive"].append(s)

            if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
                ontology_info['num_properties'] += 1
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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    # RDF properties
    for s in g.subjects(RDF.type, RDF.Property):

        if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
            if vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(OWL.deprecated, Literal(True)) and not s in g.subjects(RDF.type, OWL.DeprecatedProperty):
                domain = g.value(s, RDFS.domain)
                range_ = g.value(s, RDFS.range)

                ontology_info['num_properties'] += 1

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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }

    for s in g.subjects(RDF.type, OWL.OntologyProperty):

        if (s not in dt_props and s not in obj_props and s not in ontology_info["rdf_properties"].keys()):
            if vocab_ns and str(s).startswith(vocab_ns) and not s in g.subjects(OWL.deprecated, Literal(True)) and not s in g.subjects(RDF.type, OWL.DeprecatedProperty):
                domain = g.value(s, RDFS.domain)
                range_ = g.value(s, RDFS.range)

                ontology_info['num_properties'] += 1

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
                else:
                    ontology_info["rdf_properties"][s] = {
                        "domain": domain,
                        "range": {
                            "type": None,
                            "value": None
                        }
                    }
    

    # Disjoint via owl:disjointWith
    disjoint_pairs = set()
    for s, o in g.subject_objects(OWL.disjointWith):
        if vocab_ns and str(s).startswith(vocab_ns) and str(o).startswith(vocab_ns):
            disjoint_pairs.add(frozenset([str(s), str(o)]))

    ontology_info['disjoint_classes'] = [sorted(list(pair)) for pair in disjoint_pairs]

    # num_classes includes all classes, except deprecated ones
    ontology_info['num_all_classes'] = ontology_info["num_classes"] + len(ontology_info['deprecated_classes'])

    # num_properties includes all properties, except deprecated ones
    ontology_info['num_all_properties'] = ( ontology_info['num_properties'] + 
                                            len(ontology_info['deprecated_properties']))

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
        @prefix ex: <https://www.example.org/> . \n
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

def validate_shacl_constraints(graph_profile, data_graph_file_path, data_graph_file_format, shapes_graph, vocabs=None, config=None):
    """
    Validates a data graph against a shapes graph
    If ont_files are provided, the ontologies are incorporated to the data graph. In this case, we also generate triples
    of the form <p, rdf:type, rdf:Property> for owl properties and <c, rdf:type, rdfs:Class> for owl classes
    """

    if vocabs:

        ont_graphs = []
        for vocab in vocabs:
            file_path = config[vocab]['file_path']
            file_format = config[vocab]['file_format']
            ont_graphs.append(Graph().parse(file_path, format=file_format))

        # Create new merged graph with only class/property definitions
        merged_ont = Graph()

        # Types of OWL properties to consider
        owl_properties = {
            OWL.ObjectProperty,
            OWL.DatatypeProperty,
            OWL.FunctionalProperty,
            OWL.InverseFunctionalProperty,
            OWL.IrreflexiveProperty,
            OWL.ReflexiveProperty,
            OWL.TransitiveProperty,
            OWL.AsymmetricProperty,
            OWL.ReflexiveProperty,
            OWL.SymmetricProperty,
            OWL.DeprecatedProperty,
            OWL.OntologyProperty,
        }

        if graph_profile: # data instances
        
            # Types of OWL classes to consider
            owl_classes = {
                OWL.Class,
                OWL.DeprecatedClass,
                OWL.Restriction,
                OWL.AllDisjointClasses,
                OWL.AllDisjointProperties,
                OWL.AllDifferent,
            }

            # Not allowed
            not_allowed = {
                OWL.AnnotationProperty,
                OWL.Ontology,
            }

            # Collect all subjects to exclude (those typed as a 'not_allowed' property)
            excluded_subjects = set()
            for g in ont_graphs:
                for prop in not_allowed:
                    excluded_subjects.update(g.subjects(RDF.type, prop))

            # Add triples skipping excluded subjects
            for g in ont_graphs:
                for s, p, o in g:
                    if s not in excluded_subjects:
                        merged_ont.add((s, p, o))
                        
                        if p == RDF.type:
                            if o in owl_properties:
                                merged_ont.add((s, RDF.type, RDF.Property))
                            elif o in owl_classes:
                                merged_ont.add((s, RDF.type, RDFS.Class))
                        
                        if p == RDFS.subClassOf:
                            merged_ont.add((s, RDF.type, o))
        
        else: # vocabularies
            owl_classes = {
                OWL.Class,
                OWL.DeprecatedClass,
            }

            for g in ont_graphs:
                for s, p, o in g:
                    merged_ont.add((s, p, o))
                    
                    if p == RDF.type:
                        if o in owl_properties:
                            merged_ont.add((s, RDF.type, RDF.Property))
                        elif o in owl_classes:
                            merged_ont.add((s, RDF.type, RDFS.Class))

        data_graph = Graph().parse(data_graph_file_path, format=data_graph_file_format)

        # Merge Abox (data) + Tbox (filtered ontology)
        graph_to_validate = data_graph + merged_ont
        graph_to_validate.serialize(format="turtle", destination='aux.ttl')

        # Update for the metric calculation
        if graph_profile and 'num_entities' in graph_profile:
            graph_profile['num_entities'] += len(set(graph_to_validate.subjects(RDF.type, OWL.NamedIndividual)))
        
        graph_to_validate.serialize('aux.ttl', 'ttl')
    else:
        graph_to_validate = Graph().parse(data_graph_file_path, format=data_graph_file_format)

    conforms, report_graph, validation_report = validate(
        graph_to_validate,
        shacl_graph=shapes_graph,
        debug=False
    )

    return conforms, report_graph, validation_report, graph_profile

def get_metric_message(results_graph, result):
    
    constraint_type = results_graph.value(result, SH.sourceConstraintComponent)
    counter = -1
    # Composite constraints don't output individual validation results for each constraint inside the composite
    # They just output that the node must conform to one or more shapes in the **composite_shape**
    # Therefore, the sh:message the sh:resultMessage node

    if constraint_type in composite_components:
        metric = results_graph.value(result, SH.sourceShape).removesuffix("Shape").removeprefix("https://www.example.org/")
        result_message = results_graph.value(result, SH.resultMessage)
        
        pattern_message = r'sh:message\s+Literal\("([^"]+)"\)'
        message = ''
        match = re.search(pattern_message, result_message)
        if match:
            message = match.group(1)
    else:
        message = str(results_graph.value(result, SH.resultMessage))

    # To handle shapes for a specific property/class
    # shape message: Metric_Counter - Message

    if "_" in message: 
        # Get Metric and Counter - Message separately
        metric, counter_message = [part.strip() for part in message.split("_", 1)]
        
        # Get Counter and Message separately
        counter, message = [part.strip() for part in counter_message.split("-", 1)]
    else:
        # Remaining shapes: Metric - Message
        metric_message = message.split("-")
        metric = metric_message[0].strip()
        message = metric_message[1].strip() 
    
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
    elif metric_prefix in NUM_SUBJECTS_PER_PROPERTY:
        if "property" in info:
            return dataset_profile.get("subjects_per_property", {}).get(info['property'], 1)
    elif metric_prefix in NUM_ENTITIES_PER_CLASS:  
        if "class" in info:
            return dataset_profile.get("entities_per_class", {}).get(info['class']['first_class'], 1)

