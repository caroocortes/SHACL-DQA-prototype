from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics
from rdflib import RDF, RDFS, OWL, Graph, URIRef
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

    results = validate(
        full_graph,
        shacl_graph=shapes_graph,
        ont_graph=None,
        # inference='rdfs',
        debug=False
    )


    conforms, report_graph, report_text = results
    print(report_text)

    return conforms, report_graph

if "__main__":
    conforms, report_graph = validate_shacl_constraints('test/test_graph.ttl', 'test/test_shacl_shape.ttl', [])


# sh:or (
#         [
#             sh:path rdf:type ;
#             sh:hasValue rdfs:Class
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue rdf:Property
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue rdfs:Datatype
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:ObjectProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:DatatypeProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:Class
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:OntologyProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:Ontology
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:NamedIndividual
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:FunctionalProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:InverseFunctionalProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:IrreflexiveProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:ReflexiveProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:TransitiveProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:AnnotationProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:someValuesFrom
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:oneOf
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:allValuesFrom
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:hasValue
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:distinctMembers
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:AllDifferent
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:intersectionOf
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:unionOf
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:complementOf
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:onProperty
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:Restriction
#         ]
#         [
#             sh:path rdf:type ;
#             sh:hasValue owl:AllDisjointClasses
#         ]
# )
