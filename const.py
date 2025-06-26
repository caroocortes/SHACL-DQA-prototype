# Path to the configuration file of the dataset
CONFIG_FILE_PATH = 'config/temples.ini'

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
BINARY_METRICS_DATA = {"OpenSameAsChainsShapes", 
                       "MisplacedProperties", 
                       "SchemaCompletenessClassUsage", 
                       "DeprecatedClasses",
                        "DeprecatedProperties" }

BINARY_METRICS_METADATA = {"AvailabilityDump", 
                           "MachineReadableLicense", 
                           "AuthenticityDataset", 
                           "PresenceMetadata", 
                           "ExemplaryResources", 
                           "URIRegexPresence", 
                           "VocabularyExistence", 
                           "SerializationFormats"}

COUNT_METRICS = {"UsageExternalURIEntities", 
                 "UsageHashURIsEntities", 
                 "LabelForEntities", 
                 "URIsParametersEntitiesShape", 
                 "URIsLengthEntitiesShape",
                 "ProlixFeatures", 
                 "SelfDescriptiveFormat", 
                 "BlankNodesUsageEntities", 
                 "DifferentLanguagesLabelsEntities",
                 "DifferentLanguagesDescriptionsEntities",
                 "InterlinkingCompleteness", 
                 "MisuseOwlObjectProperties", 
                "MisuseOwlDatatypeProperties", 
                "CorrectRangeObject", 
                "CorrectRangeDatatype",
                "CorrectDomain", 
                "ReflexiveProperty", 
                "IrreflexiveProperty",
                "EntitiesDisjointClasses",
                "InverseFunctionalProperty", 
                "FunctionalProperty",
                "MalformedDatatype",
                "MemberIncompatibleDatatype"}

NUM_ENTITIES = { "UsageHashURIsEntities", 
                "LabelForEntities", 
                "URIRegexComplianceEntities", 
                "URIsLengthEntitiesShape", 
                "URIsParametersEntitiesShape",
                "ProlixFeatures", 
                "DifferentLanguagesLabelsEntities", 
                "DifferentLanguagesDescriptionsEntities",
                "SelfDescriptiveFormat", 
                "BlankNodesUsageEntities", 
                "InterlinkingCompleteness"}

NUM_CLASSES = { "LabelForClasses"}

NUM_PROPERTIES = {"LabelForProperties"}

NUM_TRIPLES_PER_PROPERTY = { "MisuseOwlObjectProperties", 
                            "MisuseOwlDatatypeProperties", 
                            "CorrectRangeObject", 
                            "CorrectRangeDatatype",
                            "CorrectDomain", 
                            "IrreflexiveProperty",
                            "InverseFunctionalProperty", 
                            "FunctionalProperty",
                            "MalformedDatatype",
                            "MemberIncompatibleDatatype"}

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
        "shape_template": "ex:MalformedDatatypeLiteralsShape\na sh:NodeShape ;\nsh:targetClass ex:Class ;\nsh:property [\nsh:path ex:SomeProperty ;\nsh:datatype DATATYPE;\nsh:pattern \"DATATYPE_PATTERN\";\n]."
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
        "shape_template": "ex:MisplacedPropertiesShape\na sh:NodeShape ;\nsh:targetNode ex:someProperty ;\nsh:property [\nsh:path [ sh:inversePath rdf:type ];\nsh:maxCount 0;\n]."
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
        "shape_template": "ex:EntitiesDisjointClassesShape\na sh:NodeShape ;\nsh:targetClass ex:SomeClass ;\nsh:not [ sh:class ex:DisjointClass ]."
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
    },
    "CorrectRangeObject": {
        "dimension": "Consistency",
        "metric_id": "CN9",
        "metric": "Correct domain and range definition.",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "CorrectRangeDatatype": {
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
        "metric": "Valid usage of irreflexive properties",
        "measure": 1,
        "shape": "",
        "message": "",
    },
    "InverseFunctionalProperty": {
        "dimension": "Consistency",
        "metric_id": "CN5",
        "metric": "Valid usage of inverse-functional properties",
        "measure": 1,
        "shape": "",
        "message": ""
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
        "description": "Verifies that the properties used in the dataset are defined in the vocabulary.",
        "metric_type": "binary",
        "metric_calculation": "1 if the property is defined, 0 otherwise",
        "meta_metric_calculation": "Number of defined properties / Number of properties used in the dataset",
        "shape_template": ""
    },
    "UndefinedClass": {
        "dimension": "Interpretability",
        "metric_id": "ITP3",
        "metric": "Invalid usage of undefined classes and properties",
        "measure": 1,
        "shape": "",
        "message": "",
        "description": "Verifies that the classes used in the dataset are defined in the vocabulary.",
        "metric_type": "binary",
        "metric_calculation": "1 if the class is defined, 0 otherwise",
        "meta_metric_calculation": "Number of defined classes / Number of classes used in the dataset",
        "shape_template": ""
    }
}