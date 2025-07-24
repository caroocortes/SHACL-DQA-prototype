from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics
from rdflib import RDF, RDFS, OWL, Graph, URIRef, SH
import time

def validate_shacl_constraints(data_graph, shape_graph, ont_files):
    
    data_graph = Graph().parse(data_graph, format='ttl')
    shapes_graph = Graph().parse(shape_graph)

    ont_graphs = []
    for file_path in ont_files:
        ont_graphs.append(Graph().parse(file_path, format='xml'))

    merged_ont = Graph()
    for g in ont_graphs:
        for triple in g:
            merged_ont.add(triple)

    owl_properties = [
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.FunctionalProperty,
        OWL.InverseFunctionalProperty,
        OWL.IrreflexiveProperty,
        OWL.ReflexiveProperty,
        OWL.TransitiveProperty,
        OWL.AllDisjointProperties,
        OWL.AnnotationProperty,
        OWL.onProperty,
        OWL.allValuesFrom,
        OWL.someValuesFrom,
        OWL.oneOf,
        OWL.members,
        OWL.distinctMembers,
        OWL.DeprecatedProperty,
        OWL.OntologyProperty,
        OWL.minCardinality,
        OWL.maxCardinality,
        OWL.intersectionOf,
        OWL.unionOf,
        OWL.complementOf,
        OWL.incompatibleWith,
        OWL.deprecated,
        OWL.topDataProperty,
        OWL.priorVersion
    ]

    for prop_type in owl_properties:
        for s in merged_ont.subjects(RDF.type, prop_type):
            merged_ont.add((s, RDF.type, RDF.Property))

    
    owl_classes = [
        OWL.Class,
        OWL.Ontology,
        OWL.AllDisjointClasses,
        OWL.Restriction,
        OWL.AllDifferent,
        OWL.NamedIndividual,
        OWL.DeprecatedClass
    ]

    for class_type in owl_classes:
        for s in merged_ont.subjects(RDF.type, class_type):
            merged_ont.add((s, RDF.type, RDFS.Class))



    full_graph = data_graph + merged_ont 
    start_time = time.time()
    results = validate(
        full_graph,
        shacl_graph=shapes_graph,
        ont_graph=None,
        # inference='rdfs',
        sparql_mode=True,
        debug=False
    )
    final_time = time.time()
    print('Total time: ', final_time - start_time)

    conforms, report_graph, report_text = results


    composite_components = { 
        SH.OrConstraintComponent,
        SH.AndConstraintComponent,
        SH.XoneConstraintComponent,
        SH.NotConstraintComponent
    }

    print(report_text)
    return conforms, report_graph

if "__main__":
    # 84 segundos solo 1 shape que hace target en las entities
    conforms, report_graph = validate_shacl_constraints('test/test_graph.ttl', 'test/test_shacl_shape.ttl', [])
