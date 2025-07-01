# Path to the configuration file of the dataset
CONFIG_FILE_PATH = 'config/pizza.ini'

# FOLDERS PATHS
# Stores templates for the dq assessment results
METRICS_TEMPLATE_FOLDER_PATH = 'dq_assessment/metrics_templates'
# Stores the result of the dq assessment
DQ_ASSESSMENT_RESULTS_FOLDER_PATH = 'datasets/{dataset_name}/results/'
# Stores the datasets
DATASETS_FOLDER_PATH = 'datasets'
# Stores the datasets vocabularies
VOCABULARIES_FOLDER_PATH = 'datasets/vocabularies'
# Stores the vocabularies' profiles
PROFILE_VOCABULARIES_FOLDER_PATH = 'profile/vocabularies'
# Stores the datasest's profiles
PROFILE_DATASETS_FOLDER_PATH = 'profile/datasets'
# Stores shapes
SHAPES_FOLDER_PATH = 'shapes'

# Stores template for the results of shapes that will be validated against the data
DQ_MEASURES_DATA_GENERIC_TEMPLATE_FILE_PATH = f'{METRICS_TEMPLATE_FOLDER_PATH}/dq_measures_data_generic_template.json'
# Stores template for the results of shapes that will be validated against the metadata
DQ_MEASURES_METADATA_TEMPLATE_FILE_PATH = f'{METRICS_TEMPLATE_FOLDER_PATH}/dq_measures_metadata_template.json'

# Stores template for the results of shapes that will be validated against the data
# but to be able to instantiate this shapes we need to extract some metadata from the
# vocabularies/ontologies
DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH = f'{METRICS_TEMPLATE_FOLDER_PATH}/dq_measures_data_specific_temp.json'

# Stores template for the resuls of shapes that will be validated against vocabularies/ontologies
DQ_MEASURES_VOCABULARIES_TEMPLATE_FILE_PATH = f'{METRICS_TEMPLATE_FOLDER_PATH}/dq_measures_vocabulary_template.json'
# Same as above but stores results for shapes that need to be instantiated
DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH = f'{METRICS_TEMPLATE_FOLDER_PATH}/dq_measures_vocabulary_specific_temp.json'

# Helper data structures for Data Quality Assessment
BINARY_METRICS_DATA = {"MisplacedProperties", 
                        "MisplacedClasses",
                        "SchemaCompletenessClassUsage", 
                        "DeprecatedClasses",
                        "InverseFunctionalPropertyUniqueness",
                        "SelfDescriptiveFormatProperties" }

BINARY_METRICS_METADATA = {"AvailabilityDump", 
                           "MachineReadableLicense", 
                           "AuthenticityOfDatasetSource", 
                           "AuthenticityOfDatasetAuthor",
                           "PresenceMetadata", 
                           "ExemplaryResources", 
                           "URIRegexPressence", 
                           "URISpacePressence",
                           "VocabularyExistence", 
                           "SerializationFormats"}

COUNT_METRICS = {"UsageExternalURIEntities", 
                 "UsageHashURIsEntities", 
                 "LabelForEntities", 
                 "URIsParametersEntities", 
                 "URIsLengthEntities",
                 "ProlixFeatures", 
                 "SelfDescriptiveFormat", 
                 "BlankNodesUsageEntities", 
                 "DifferentLanguagesLabelsEntities",
                 "DifferentLanguagesDescriptionsEntities",
                 "InterlinkingCompleteness", 
                 "MisuseOwlObjectProperties", 
                "MisuseOwlDatatypeProperties", 
                "CorrectRange", 
                "CorrectDomain", 
                "IrreflexiveProperty",
                "EntitiesDisjointClasses",
                "FunctionalProperty",
                "MalformedDatatype",
                "MemberIncompatibleDatatype", 
                "DeprecatedProperties",
                "URISpaceComplianceEntities",
                "URIRegexComplianceEntities"}

NUM_ENTITIES = { "UsageHashURIsEntities", 
                "LabelForEntities", 
                "URIRegexComplianceEntities", 
                "URISpaceComplianceEntities",
                "URIsLengthEntities", 
                "URIsParametersEntities",
                "ProlixFeatures", 
                "DifferentLanguagesLabelsEntities", 
                "DifferentLanguagesDescriptionsEntities",
                "SelfDescriptiveFormat", 
                "BlankNodesUsageEntities", 
                "InterlinkingCompleteness", 
                "DeprecatedProperties"}

NUM_CLASSES = { "LabelForClasses"}

NUM_PROPERTIES = {"LabelForProperties"}

NUM_SUBJECTS_PER_PROPERTY = {"FunctionalProperty", 
                            "IrreflexiveProperty", 
                            "CorrectRange", 
                            "CorrectDomain", 
                            "MisuseOwlObjectProperties", 
                            "MisuseOwlDatatypeProperties", 
                            "MalformedDatatype",
                            "MemberIncompatibleDatatype",
                            "UsageExternalURIEntities"}

NUM_ENTITIES_PER_CLASS = { "EntitiesDisjointClasses"}

# Regex patterns for datatypes (Malformed datatype metric)
REGEX_PATTERNS_DICT = {
    'http://www.w3.org/2001/XMLSchema#integer': r'^[\-+]?[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#double': r'^(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|(\+|-)?INF|NaN$',
    'http://www.w3.org/2001/XMLSchema#float': r'^(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|(\+|-)?INF|NaN$',
    'http://www.w3.org/2001/XMLSchema#any': r'^.*$',
    'http://www.w3.org/2001/XMLSchema#decimal': r'^(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)$',
    'http://www.w3.org/2001/XMLSchema#time': r'^(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#date': r'^-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#dateTime': r'^-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#dateTimeStamp': r'^-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#string': r'^.*$',
    'http://www.w3.org/2001/XMLSchema#gYear': r'^-?([1-9][0-9]{3,}|0[0-9]{3})(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#gMonth': r'^--(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#gDay': r'^---(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#gYearMonth': r'^-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#gMonthDay': r'^--(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$',
    'http://www.w3.org/2001/XMLSchema#duration': r'^-?P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]+)?S)?)?$',
    'http://www.w3.org/2001/XMLSchema#yearMonthDuration': r'^-?P([0-9]+Y)?([0-9]+M)?$',
    'http://www.w3.org/2001/XMLSchema#dayTimeDuration': r'^-?P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]+)?S)?)?$',
    'http://www.w3.org/2001/XMLSchema#byte': r'^[\-+]?[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#short': r'^[\-+]?[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#long': r'^[\-+]?[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#unsignedByte': r'^[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#unsignedShort': r'^[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#unsignedInt': r'^[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#unsignedLong': r'^[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#positiveInteger': r'^[1-9][0-9]*$',
    'http://www.w3.org/2001/XMLSchema#nonNegativeInteger': r'^[0-9]+$',
    'http://www.w3.org/2001/XMLSchema#negativeInteger': r'^-[1-9][0-9]*$',
    'http://www.w3.org/2001/XMLSchema#nonPositiveInteger': r'^(-[0-9]+|0)$',
    'http://www.w3.org/2001/XMLSchema#hexBinary': r'^([0-9a-fA-F]{2})*$',
    'http://www.w3.org/2001/XMLSchema#base64Binary': r'^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$',
    'http://www.w3.org/2001/XMLSchema#language': r'^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$',
    'http://www.w3.org/2001/XMLSchema#normalizedString': r'^[^\s]+$',
    'http://www.w3.org/2001/XMLSchema#NMTOKEN': r'^\w+$',
    'http://www.w3.org/2001/XMLSchema#Name': r'^[A-Za-z_][A-Za-z0-9._-]*$',
    'http://www.w3.org/2001/XMLSchema#NCName': r'^[A-Za-z_][A-Za-z0-9._-]*$',
    'http://www.w3.org/2001/XMLSchema#boolean': r'^(true|false|0|1)$',
}

# DQ initial results for metrics that need instantiation
DQ_MEASURES_DATA_SPECIFIC = {
    "MalformedDatatypeLiterals": {
        "dimension": "Syntactic Validity",
        "metric_id": "SV3",
        "metric": "No malformed datatype literals",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies that literals comply with their expected patterns",
        "metric_type": "count",
        "meta_metric_calculation": "Number of properties used with a wellformed datatype / Number of properties whose range is a datatype",
        "metric_calculation": "1 - (Number of violations / Number of triples that use the property)",
        "shape_template": "ex:MalformedDatatypeLiteralsShape\na sh:NodeShape ;\nsh:targetClass ex:Class ;\nsh:property [\n\tsh:path ex:SomeProperty ;\n\tsh:datatype DATATYPE ;\n\tsh:pattern \"DATATYPE_PATTERN\" ;\n]."
    },
    "MisplacedProperties": {
        "dimension": "Consistency",
        "metric_id": "CN2",
        "metric": "No misplaced classes or properties",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies that properties aren't used as classes",
        "metric_type": "binary",
        "metric_calculation": "0 if property is used as a class, 1 otherwise.",
        "meta_metric_calculation": "Number of correctly used properties / Number of properties defined in vocabularies",
        "shape_template": "ex:MisplacedPropertiesShape\na sh:NodeShape ;\nsh:targetNode ex:someProperty ;\nsh:property [\n\tsh:path [ sh:inversePath rdf:type ] ;\n\tsh:maxCount 0 ;\n]."
    },
    "MisplacedClasses": {
        "dimension": "Consistency",
        "metric_id": "CN2",
        "metric": "No misplaced classes or properties",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies that classes aren't used as properties",
        "metric_type": "binary",
        "metric_calculation": "0 if class is used as property, 1 otherwise.",
        "meta_metric_calculation": "Number of correctly used classes / Number of classes defined in vocabularies",
        "shape_template": "ex:MisplacedClassesShape\na sh:NodeShape ;\nsh:targetSubjectsOf TYPE_PROPERTY ;\nsh:or (\n[\n\tsh:path rdf:type ;\n\tsh:hasValue rdfs:Class ;\n]\n[\n\tsh:path rdf:type ;\n\tsh:hasValue rdf:Property ;\n]\n[\n\tsh:path CLASS_URI ;\n\tsh:maxCount 0 ;\n]\n) ."
    },
    "EntitiesDisjointClasses": {
        "dimension": "Consistency",
        "metric_id": "CN1",
        "metric": "No use of entities as members of disjoint classes",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies there are no entities that are members of disjoint classes.",
        "metric_type": "count",
        "metric_calculation": "1 - (Number of violations / Number of entities of the target class)",
        "meta_metric_calculation": "Number of classes with no member as instance of a disjoint class / Number of classes",
        "shape_template": "ex:EntitiesDisjointClassesShape\na sh:NodeShape ;\nsh:targetClass ex:SomeClass ;\nsh:not [\n\tsh:class ex:DisjointClass\n]."
    },
    "MisuseOwlObjectProperties": {
        "dimension": "Consistency",
        "metric_id": "CN3",
        "metric": "No misuse of owl:DatatypeProperty or owl:ObjectProperty",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "MisuseOwlDatatypeProperties": {
        "dimension": "Consistency",
        "metric_id": "CN3",
        "metric": "No misuse of owl:DatatypeProperty or owl:ObjectProperty",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "DeprecatedProperties": {
        "dimension": "Consistency",
        "metric_id": "CN4",
        "metric": "Members of owl:DeprecatedClass or owl:DeprecatedProperty not used",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "DeprecatedClasses": {
        "dimension": "Consistency",
        "metric_id": "CN4",
        "metric": "Members of owl:DeprecatedClass or owl:DeprecatedProperty not used",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies that deprecated classes aren't used",
        'metric_type': 'binary',
        'metric_calculation': '1 if no deprecated classes are used, 0 otherwise',
        'meta_metric_calculation': '',
        'shape_name': 'DeprecatedClassesShape',
        'shape_template': "ex:DeprecatedClassesShape\na sh:NodeShape ;\nsh:targetSubjectsOf TYPE_PROPERTY ;\nsh:or (\n[\n\tsh:path rdf:type ;\n\tsh:hasValue rdfs:Class ;\n]\n[\n\tsh:path rdf:type ;\n\tsh:hasValue rdf:Property ;\n]\n[\n\tsh:path rdf:type ;\n\tsh:not [\n\t\tsh:in ( CLASSES_LIST );\n\t] ;\n]\n) .",
        'violations': '',
        'num_violations': '',
        'vocab': ''
    },
    "CorrectRange": {
        "dimension": "Consistency",
        "metric_id": "CN9",
        "metric": "Correct domain and range definition.",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "CorrectDomain": {
        "dimension": "Consistency",
        "metric_id": "CN9",
        "metric": "Correct domain and range definition.",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "IrreflexiveProperty": {
        "dimension": "Consistency",
        "metric_id": "CN10",
        "metric": "No inconsistent values",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "InverseFunctionalPropertyUniqueness": {
        'dimension': 'Consistency',
        'metric_id': 'CN5',
        'metric': 'Valid usage of inverse-functional properties',
        'description': 'Verifies the correct usage of inverse-functional properties.',
        'measure': 1,
        'message': '',
        'metric_type': 'binary',
        'metric_calculation': '1 if the inverse functional property is correctly used, 0 otherwise',
        "meta_metric_calculation": "Number of inverse-functional properties correctly used / Number of inverse-functional properties",
        'shape_name': 'InverseFunctionalPropertyUniquenessShape',
        'shape_template': 'ex:InverseFunctionalPropertyUniquenessShape\na sh:NodeShape ;\nsh:targetObjectsOf PROPERTY_URI ;\nsh:property [\n\tsh:path [ sh:inversePath PROPERTY_URI ];\n\tsh:maxCount 1 ;\n].',
        'violations': '',
        'num_violations': '',
        'vocab': ''
    },
    "FunctionalProperty": {
        "dimension": "Consistency",
        "metric_id": "CN10",
        "metric": "No inconsistent values",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "SchemaCompletenessClassUsage": {
        "dimension": "Completeness",
        "metric_id": "CP1",
        "metric": "Schema completeness",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "MemberIncompatibleDatatype": {
        "dimension": "Syntactic Validity",
        "metric_id": "SV3",
        "metric": "No malformed datatype literals",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "MalformedDatatype": {
        "dimension": "Syntactic Validity",
        "metric_id": "SV3",
        "metric": "No malformed datatype literals",
        "measure": 1,
        "shape": "",
        "message": ""
    },
    "SelfDescriptiveFormatProperties": {
        "dimension": "Interpretability",
        "metric_id": "ITP1",
        "metric": "Use of self-descriptive formats",
        "measure": 1,
        "shape": "",
        "message": ""
    }
}

DQ_MEASURES_VOCABULARY_SPECIFIC = {
    "UndefinedProperty": {
        "dimension": "Interpretability",
        "metric_id": "ITP3",
        "metric": "Invalid usage of undefined classes and properties",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "UndefinedClass": {
        "dimension": "Interpretability",
        "metric_id": "ITP3",
        "metric": "Invalid usage of undefined classes and properties",
        "measure": 1,
        "shape": "",
        "message": ""
    }
}

METRIC_COVERAGE = [
    ["Availability", "A1", "accessibility of the SPARQL endpoint and the server", "No"],
    ["Availability", "A2", "accessibility of the RDF dumps", "Partial"],
    ["Availability", "A3", "dereferenceability of the URI", "No"],
    ["Availability", "A4", "no misreported content types", "No"],
    ["Availability", "A5", "dereferenced forward-links", "No"],
    ["Licensing", "L1", "machine-readable indication of a license in the VoID description of the dataset", "Yes"],
    ["Licensing", "L2", "human-readable indication of a license in the documentation of the dataset", "No"],
    ["Licensing", "L3", "specifying the correct license", "No"],
    ["Interlinking", "I1", "detection of good quality interlinks", "No"],
    ["Interlinking", "I2", "existence of links to external data providers", "Yes"],
    ["Interlinking", "I3", "dereferenced back-links", "No"],
    ["Security", "SE1", "usage of digital signatures", "Yes"],
    ["Security", "SE2", "authenticity of the dataset", "Yes"],
    ["Performance", "P1", "usage of slash-URIs", "Yes"],
    ["Performance", "P2", "low latency", "No"],
    ["Performance", "P3", "High throughput", "No"],
    ["Performance", "P4", "Scalability of a data source", "No"],
    ["Relevancy", "R1", "Relevant terms within meta-information attributes", "No"],
    ["Relevancy", "R2", "coverage", "Partial"],
    ["Understandability", "U1", "Human-readable labelling of classes, properties and entities as well as presence of metadata", "Partial"],
    ["Understandability", "U2", "Indication of one or more exemplary URIs", "Yes"],
    ["Understandability", "U3", "Indication of a regular expression that matches the URIs of a dataset", "Yes"],
    ["Understandability", "U4", "Indication of an exemplary SPARQL query", "No"],
    ["Understandability", "U5", "Indication of the vocabularies used in the dataset", "Yes"],
    ["Understandability", "U6", "Provision of message boards and mailing lists", "No"],
    ["Trustworthiness", "T1", "Trustworthiness of statements", "No"],
    ["Trustworthiness", "T2", "trustworthiness through reasoning", "Partial"],
    ["Trustworthiness", "T3", "trustworthiness of statements, datasets and rules", "Partial"],
    ["Trustworthiness", "T4", "trustworthiness of a resource", "No"],
    ["Trustworthiness", "T5", "trustworthiness of the information provider", "Partial"],
    ["Trustworthiness", "T6", "trustworthiness of information provided (content trust)", "Yes"],
    ["Trustworthiness", "T7", "reputation of the dataset", "No"],
    ["Timeliness", "TI1", "freshness of datasets based on currency and volatility", "Partial"],
    ["Timeliness", "TI2", "freshness of datasets based on their data source", "Partial"],
    ["Representational conciseness", "RC1", "keeping URIs short", "Yes"],
    ["Representational conciseness", "RC2", "no use of prolix RDF features", "Yes"],
    ["Interoperability", "IO1", "Re-use of existing terms", "Yes"],
    ["Interoperability", "IO2", "Re-use of existing vocabularies", "Partial"],
    ["Versatility", "V1", "Provision of the data in different serialization formats", "Yes"],
    ["Versatility", "V2", "checking whether data is available in different languages", "Yes"],
    ["Interpretability", "IP1", "use of self-descriptive formats", "Yes"],
    ["Interpretability", "IP2", "detecting the interpretability of data", "Partial"],
    ["Interpretability", "IP3", "invalid usage of undefined classes and properties", "Yes"],
    ["Interpretability", "IP4", "no misinterpretation of missing values", "Yes"],
    ["Syntactic validity", "SV1", "no syntax errors of the documents", "No"],
    ["Syntactic validity", "SV2", "Syntactically accurate values", "Partial"],
    ["Syntactic validity", "SV3", "no malformed datatype literals", "Yes"],
    ["Semantic accuracy", "SA1", "no outliers", "No"],
    ["Semantic accuracy", "SA2", "no inaccurate values", "Partial"],
    ["Semantic accuracy", "SA3", "no inaccurate annotations, labellings or classifications", "Partial"],
    ["Semantic accuracy", "SA4", "no misuse of properties", "No"],
    ["Semantic accuracy", "SA5", "detection of valid rules", "No"],
    ["Consistency", "C1", "no use of entities as members of disjoint classes", "Yes"],
    ["Consistency", "C2", "no misplaced classes or properties", "No"],
    ["Consistency", "C3", "no misuse of owl:DatatypeProperty or owl:ObjectProperty", "Yes"],
    ["Consistency", "C4", "members of owl:DeprecatedClass or owl:DeprecatedProperty not used", "Yes"],
    ["Consistency", "C5", "valid usage of inverse-functional properties", "Partial"],
    ["Consistency", "C6", "absence of ontology hijacking", "No"],
    ["Consistency", "C7", "no negative dependencies/correlation among properties", "Yes"],
    ["Consistency", "C8", "no inconsistencies in spatial data", "No"],
    ["Consistency", "C9", "correct domain and range definition", "Yes"],
    ["Consistency", "C10", "no inconsistent values", "Partial"],
    ["Conciseness", "CO1", "high intensional conciseness", "No"],
    ["Conciseness", "CO2", "high extensional conciseness", "Partial"],
    ["Conciseness", "CO3", "usage of unambiguous annotations/labels", "No"],
    ["Completeness", "CM1", "schema completeness", "Partial"],
    ["Completeness", "CM2", "property completeness", "Partial"],
    ["Completeness", "CM3", "population completeness", "No"],
    ["Completeness", "CM4", "interlinking completeness", "Partial"],
]