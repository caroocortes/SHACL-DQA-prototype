import configparser
import logging
import csv
from jinja2 import Environment, FileSystemLoader
import time
import glob
from collections import defaultdict
from rdflib.namespace import DCTERMS, VOID, SH, FOAF

from shacl_shape_builder import SHACLShapeBuilder
from utils import *

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="rdflib.term")

logging.basicConfig(level=logging.INFO)

class DQAssessment:

    def __init__(self, config_path, 
                 metadata_shapes=True, 
                 data_shapes=True, 
                 vocab_shapes=True):
        
        self.metadata_shapes = metadata_shapes
        self.data_shapes = data_shapes
        self.config = self._load_config(config_path)
        self.vocab_shapes = vocab_shapes
        self._init_paths_and_params()

        self.shape_builder = SHACLShapeBuilder(self)
        
        self.counter_shapes = 0
        self.total_elapsed_time = 0
        self.data_shapes_elapsed_time = 0
        self.vocab_shapes_elapsed_time = 0
        self.metadata_shapes_elapsed_time = 0
        self.graph_profile = None

    def _load_config(self, path):
        try:
            config = configparser.ConfigParser()
            read_files = config.read(path)

            if not read_files:
                raise FileNotFoundError(f"Config file not found at path: {path}")

            return config

        except configparser.ParsingError as e:
            raise ValueError(f"Failed to parse config file '{path}': {e}")

    def _init_paths_and_params(self):
        settings = self.config['settings']

        self.graph_file_path = settings['graph_file']
        self.vocab_names = [v.strip() for v in settings["vocabularies"].split(",")]

        self.graph_file_path = settings['graph_file']
        self.graph_file_format = settings['graph_file_format']
        self.dataset_name = settings["dataset_name"]
        self.dataset_name = self.dataset_name.lower().replace(" ", "_")

        self.metadata_file = settings['metadata_file']
        self.metadata_file_format = settings['metadata_file_format']

        # Parameters for SHACL shapes
        self.metadata_class = settings['metadata_class']
        self.type_property = settings['type_property']
        self.labeling_property = settings['labeling_property']
        self.description_property = settings['description_property']
        self.interlinking_property = settings['interlinking_property']
        self.base_namespace = settings['base_namespace'] # this is not being used!!!!! I think I didn't implement the shape that checks for the uriSpace...
        self.uris_max_length = settings['uris_max_length']
        self.vocab_names = [v.strip() for v in settings["vocabularies"].split(",")]

        # Shapes templates
        env = Environment(loader=FileSystemLoader("dq_assessment/shapes"))
        self.data_template = env.get_template("data_shapes.template.ttl")
        self.metadata_template = env.get_template("metadata_shapes.template.ttl")
        self.vocabs_template = env.get_template("vocabulary_shapes.template.ttl")

        self.regex_pattern = None
        self.uri_space = None

        self.aggregate_dict_counter = {}


    def run(self):

        self.profile_data()
        logging.info(f"Finished profiling graph and vocabularies. Saved results in {PROFILE_DATASETS_FOLDER_PATH} & {PROFILE_VOCABULARIES_FOLDER_PATH}")
        
        initial_time = time.time() # start of validation
    
        # ---- Validate metadata shapes ----
        if self.metadata_shapes and self.metadata_file:
            validation_time = self.validate_metadata_shapes()
            self.metadata_shapes_elapsed_time = validation_time
            logging.info(f"Finished validating metadata shapes. \n Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}dq_assessment_{self.dataset_name}_metadata.json'. Validation time: {validation_time}")

        # ---- Validate data shapes ----
        if self.data_shapes:
            validation_time = self.validate_data_shapes()
            self.data_shapes_elapsed_time = validation_time
            logging.info(f"Finished validating data shapes. Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}/dq_assessment_{self.dataset_name}_data.json'. Validation time: {validation_time}")

        # ---- Validate shapes against vocabularies ----
        if self.vocab_shapes:
            validation_time = self.validate_vocabulary_shapes()
            self.vocab_shapes_elapsed_time = validation_time
            logging.info(f"Finished validating shapes against vocabularies. Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}dq_assessment_[vocab_name].json'. Validation time: {validation_time}")

        final_time = time.time() # end of validation
        self.total_elapsed_time = final_time - initial_time
        logging.info(f"Total elapsed time: {self.total_elapsed_time}")

        # Remove specific .json result file created for shapes that need instantiation from vocabularies
        if os.path.exists(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH):
            os.remove(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH)

        if os.path.exists(DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH):
            os.remove(DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH)

        self.create_dq_results_csv()


    def profile_data(self):
        if self.data_shapes:
            graph_profile_output_path = f'{PROFILE_DATASETS_FOLDER_PATH}/{self.dataset_name}.json'
            self.graph_profile = profile_graph(self, graph_profile_output_path)
            logging.info(f"Graph profile saved in {graph_profile_output_path}.")

        if self.vocab_shapes:
            # Maps a vocabulary with its namespace
            dict_vocab_file = {}
            for vocab in self.vocab_names:
                
                vocab_ns = profile_vocab(self, vocab)
                vocab_name = self.config[vocab]["vocab_name"]
                dict_vocab_file[vocab_name] = vocab_ns
                
            self.dict_vocab_ns_file = dict_vocab_file

    def validate_metadata_shapes(self):
        """ 
            Validates shapes against the metadata file 
        """

        validation_time = 0

        # Generate metadata shapes
        shape_graph = create_shape_graph(self.metadata_template.module.metadata_shape(self.metadata_class))

        # Save shapes
        folder_path = f'{DATASETS_FOLDER_PATH}/{self.dataset_name}/shapes'
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/metadata_shapes.ttl'
        shape_graph.serialize(destination=file_path, format='turtle')
        logging.info(f'Metadata shapes for dataset {self.dataset_name} saved in {file_path}')
        
        # Run validation 
        _, val_graph, _ , _, validation_time = validate_shacl_constraints(None, self.metadata_file, self.metadata_file_format, shape_graph, vocabs=None, config=None)
        # Process & store validation results
        self.process_validation_result_metadata(val_graph)
        
        logging.info(f"Finished DQA for metadata file. Results saved in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}/dq_assessment_{self.dataset_name}_metadata.json'. \n")

        return validation_time

    def validate_vocabulary_shapes(self):

        validation_time = 0
        # Stores for each vocabulary the classes used in the dataset
        class_vocab_map = {}
        for class_ in self.graph_profile['classes']:
            class_ns = get_ns(class_)

            for vocab in self.vocab_names:
                vocab_name = self.config[vocab]["vocab_name"]
                vocab_ns = self.dict_vocab_ns_file[vocab_name] 

                if class_ns == vocab_ns:
                    if vocab_name not in class_vocab_map:
                        class_vocab_map[vocab_name] = []
                    class_vocab_map[vocab_name].append(class_)

        # Stores for each vocabulary the properties used in the dataset
        property_vocab_map = {}
        for prop_ in self.graph_profile['properties']:
            prop_ns = get_ns(prop_)
            for vocab in self.vocab_names:
                vocab_name = self.config[vocab]["vocab_name"]
                vocab_ns = self.dict_vocab_ns_file[vocab_name]

                if prop_ns == vocab_ns:
                    if vocab_name not in property_vocab_map:
                        property_vocab_map[vocab_name] = []
                    property_vocab_map[vocab_name].append(prop_)

        self.counter_vocab_map = {}
        for vocab in self.vocab_names:
            vocab_name = self.config[vocab]['vocab_name']

            # Instantiate shapes
            shacl_shapes = self.shape_builder.vocabulary_shapes(self, vocab, property_vocab_map, class_vocab_map)

            # Create shape graph
            shape_graph = create_shape_graph(shacl_shapes)

            # Store shapes
            folder_path = f'{DATASETS_FOLDER_PATH}/{self.dataset_name}/shapes'
            os.makedirs(folder_path, exist_ok=True)
            file_path = f'{folder_path}/vocabulary_shapes_{vocab_name}.ttl'
            shape_graph.serialize(destination=file_path, format='turtle')
            logging.info(f'Shapes for vocabulary {self.dataset_name} saved in {file_path}')

            # Validate shapes
            file_path = self.config[vocab]["file_path"]
            file_format = self.config[vocab]["file_format"]
            _, val_graph, _, _, validation_time = validate_shacl_constraints(None, file_path, file_format, shape_graph, vocabs=[vocab], config=self.config)

            with open(f'{PROFILE_VOCABULARIES_FOLDER_PATH}/{vocab_name}.json', 'r', encoding='utf-8') as f:
                vocab_profile = json.load(f)

            # Process validation results
            self.process_validation_result_vocabularies(val_graph, vocab_name, vocab_profile, property_vocab_map, class_vocab_map)

        return validation_time

    def validate_data_shapes(self):
        """
            Validates data shapes
        """
        validation_time = 0

        # Instantiate shapes
        accessibility_shapes = self.shape_builder.accessibility_data_shapes()
        self.regex_pattern, self.uri_space, contextual_shapes = self.shape_builder.contextual_data_shapes()
        representational_shapes, self.shape_property_map_representational = self.shape_builder.representational_data_shapes(self.graph_profile)

        # Update graph_profile because it gets updated inside intrinsic_data_shapes
        intrinsic_shapes, self.graph_profile, self.shape_property_map_intrinsic, self.shape_class_map = self.shape_builder.intrinsic_data_shapes(self.graph_profile)

        shacl_shapes = (accessibility_shapes + '\n' + 
                        contextual_shapes + '\n' +
                        representational_shapes + '\n' +
                        intrinsic_shapes
                    )

        # Create shapes graph
        shape_graph = create_shape_graph(shacl_shapes)

        # Save shapes graph
        folder_path = f'{DATASETS_FOLDER_PATH}/{self.dataset_name}/shapes'
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/data_shapes.ttl'
        shape_graph.serialize(destination=file_path, format='turtle')
        logging.info(f'Data shapes for dataset {self.dataset_name} saved in {file_path}')

        _, val_graph, _, self.graph_profile, validation_time = validate_shacl_constraints(self.graph_profile, self.graph_file_path, self.graph_file_format, shape_graph, self.vocab_names, self.config)

        # Process validation results
        results = self.process_validation_result_data(val_graph)
        
        # Store dq assessment results
        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/dq_assessment_{self.dataset_name}_data.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)

        return validation_time

    def process_validation_result_metadata(self, results_graph):
        """
            Process validation results for shapes validated against the metadata
        """
        
        with open(DQ_MEASURES_METADATA_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
            results = json.load(f)

        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/dq_assessment_{self.dataset_name}_metadata.json'

        validation_results = results_graph.subjects(RDF.type, SH.ValidationResult)
        if not any(validation_results):
            # If no validation results, save template files without updating measures
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            return

        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            metric, message, _ = get_metric_message(results_graph, result)    
            # All metadata metrics are binary, so if there's a validation result, 
            # it means the measure is 0

            # Had to separate this shape so I could get the specific violation
            if metric == 'AuthenticityOfDatasetAuthor' or metric == 'AuthenticityOfDatasetSource':
                metric = 'AuthenticityOfDataset'

            if metric == "DatasetMetadata": # contains multiple constraints
                result_path = results_graph.value(result, SH.resultPath)
                if result_path == DCTERMS.title or result_path == DCTERMS.description or result_path == FOAF.homepage:
                    metric = 'PresenceMetadata'
                if result_path == VOID.exampleResource:
                    metric = 'ExemplaryResources'
                if result_path == VOID.vocabulary:
                    metric = 'VocabularyExistence'
                if result_path == VOID.feature:
                    metric = 'SerializationFormats'
                if result_path == VOID.uriRegexPattern:
                    metric = 'URIRegexPressence'
                if result_path == VOID.uriSpace:
                    metric = 'URISpacePressence'
                if result_path == DCTERMS.license:
                    metric = 'MachineReadableLicense'

            results[metric]["measure"] = 0

            constraint_type = results_graph.value(result, SH.sourceConstraintComponent)
            if constraint_type != SH.MinCountConstraintComponent and constraint_type != SH.OrConstraintComponent:
                # Metadata shapes have constraints to check for the correctness of the values of properties
                new_message = 'The property is present but the value is incorrect.'
                results[metric]["message"] = new_message
            else:
                # If the constraint is a MinCount, it means the property is not present
                results[metric]["message"] = message
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)


    def process_validation_result_vocabularies(self, results_graph, vocab, vocab_profile, property_vocab_map, class_vocab_map):

        with open(DQ_MEASURES_VOCABULARIES_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
            metrics_generic = json.load(f)
  
        if os.path.exists(DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH):
            with open(DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
                metrics_specific = json.load(f)
        
        results = metrics_generic | metrics_specific

        violating_entities_per_shape = defaultdict(set)

        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        file_path = f'{folder_path}dq_assessment_vocabularies_{vocab}.json'
        os.makedirs(folder_path, exist_ok=True)
        validation_results = results_graph.subjects(RDF.type, SH.ValidationResult)
        if not any(validation_results):
            # If no validation results, save template files without updating measures
            for metric, info in results.items():
                info['vocab'] = vocab
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            return

        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            metric, message, counter = get_metric_message(results_graph, result)

            focus_node = results_graph.value(result, SH.focusNode)

            if metric.startswith("UndefinedProperty"):
                metric = f'{metric}_{counter}'
                # check that the property is actually from the vocabulary
                # some vocabularies define properties from other vocabularies as 
                # annotation properties 
                
                results[metric]["property"] = focus_node
                results[metric]["measure"] = 0
              
            elif metric.startswith("UndefinedClass"):
                metric = f'{metric}_{counter}'
                # check that the class is actually from the vocabulary
                
                results[metric]["class"] = focus_node
                results[metric]["measure"] = 0
                
            elif metric and focus_node:
                # consider unique focus nodes for each metric
                if metric not in violating_entities_per_shape:
                    violating_entities_per_shape[metric] = set()
                
                # TODO: check if this is needed
                # check that the class/property is actually from the vocabulary
                violating_entities_per_shape[metric].add(focus_node)

            if results[metric]["message"] == "":
                results[metric]["message"] = message
        
        for metric, nodes in violating_entities_per_shape.items():
            count = len(nodes)
            if metric == 'LabelForClasses':
                denominator = vocab_profile.get("num_all_classes", 1) + vocab_profile.get("num_other_classes", 1)
            elif metric == 'LabelForProperties':
                denominator = vocab_profile.get("num_all_properties", 1)+ vocab_profile.get("num_other_properties", 1)
            
            ratio = 1 - (count / denominator)
            results[metric]["measure"] = ratio
            results[metric]['violations'] = '; '.join(nodes)
            results[metric]['num_violations'] = count
        
        for metric, info in results.items():
            info['vocab'] = vocab

        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        file_path = f'{folder_path}dq_assessment_vocabularies_{vocab}.json'
        os.makedirs(folder_path, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)


    def process_validation_result_data(self, results_graph):
        """
        Process validation results for shapes validated against the data.
        """
        
        violating_entities_per_shape = defaultdict(lambda: {"entities": set()})
        
        with open(DQ_MEASURES_DATA_GENERIC_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
            metrics_generic = json.load(f)
        
        metrics_specific = {}
        if os.path.exists(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH):
            with open(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
                metrics_specific = json.load(f)

        results = metrics_generic | metrics_specific

        if self.regex_pattern is None:
            # There's no regex pattern provided for the URIs, 
            # hence, we don't need to calculate the URIRegexComplianceEntities,
            results.pop("URIRegexComplianceEntities")

        if self.uri_space is None:
            # There's no uri space provided for the URIs, 
            # hence, we don't need to calculate the URISpaceComplianceEntities,
            results.pop("URISpaceComplianceEntities")
        
        if not self.labeling_property:
            results.pop('DifferentLanguagesLabelsEntities')

        if not self.description_property:
            results.pop('DifferentLanguagesDescriptionsEntities')

        validation_results = results_graph.subjects(RDF.type, SH.ValidationResult)
        if not any(validation_results):
            return results
        
        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            
            constraint_type = results_graph.value(result, SH.sourceConstraintComponent)
            metric, message, counter = get_metric_message(results_graph, result)

            if metric in BINARY_METRICS_DATA:
                if counter != -1 and not metric.startswith("Deprecated"):
                    metric = f'{metric}_{counter}'
                
                if metric.startswith("MisplacedProperties") or metric.startswith("InverseFunctionalProperty"):
                    results[metric]["property"] = self.shape_property_map_intrinsic[int(counter)]

                if metric.startswith("SelfDescriptiveFormatProperties"):
                    results[metric]["property"] = self.shape_property_map_representational[int(counter)]
              
                if metric.startswith("SchemaCompleteness") or metric.startswith("MisplacedClasses"):
                    results[metric]["class"] = self.shape_class_map[int(counter)]
                
                # For deprecated classes violations are the entities that use the class
                # For inverse functional properties violations are the entities that use the property
                # For self-descriptive format properties violations are the values of the property that aren't IRIs
                # For misplaced classes violations are the entities that use the class
                if (metric.startswith("DeprecatedClasses") or 
                    metric.startswith("InverseFunctionalProperty") or 
                    metric.startswith("SelfDescriptiveFormatProperties")):
                    
                    focus_node = results_graph.value(result, SH.focusNode)
                    if "violations" not in results[metric] or results[metric]['violations'] == '':
                        results[metric]['violations'] = str(focus_node.toPython())
                        
                    elif results[metric]['violations'] != '':
                        results[metric]['violations'] += ';' + str(focus_node.toPython())

                results[metric]["measure"] = 0 
            
            elif metric in COUNT_METRICS:

                if metric in NUM_SUBJECTS_PER_PROPERTY:
                    
                    # if an entity uses the property with the same value more than once -> 
                    # the validation result outputs a single result per entity

                    # if the entity uses the property with different values and they all raise a validation result
                    # -> i have to consider unique focus nodes

                    #  I instantiate the "entities" with a set
                    if counter != -1:
                        metric = f'{metric}_{counter}'
                    if metric not in violating_entities_per_shape:
                        if metric == 'UsageExternalURIEntities':
                            violating_entities_per_shape[metric] = {
                                "entities": set(),
                                "property": self.interlinking_property
                            }
                        elif metric == 'DifferentLanguagesLabelsEntities':
                            violating_entities_per_shape[metric] = {
                                "entities": set(),
                                "property": self.labeling_property
                            }
                        elif metric == 'DifferentLanguagesDescriptionsEntities':
                            violating_entities_per_shape[metric] = {
                                "entities": set(),
                                "property": self.description_property
                            }
                        else:
                            violating_entities_per_shape[metric] = {
                                "entities": set(),
                                "property": self.shape_property_map_intrinsic[int(counter)]
                            }

                elif metric in NUM_ENTITIES_PER_CLASS:
                    if counter != -1:
                        metric = f'{metric}_{counter}'
    
                    if metric not in violating_entities_per_shape:
   
                        violating_entities_per_shape[metric] = {
                            "entities": set(),
                            "class": self.shape_class_map[int(counter)]
                        }
                else:
                    if counter != -1:
                        metric = f'{metric}_{counter}'

                    if metric not in violating_entities_per_shape:
                        
                        if metric.startswith("DeprecatedProp"):
                            violating_entities_per_shape[metric] = {
                                "entities": set(),
                                "property": self.shape_property_map_intrinsic[int(counter)]
                            }
                        else:
                            violating_entities_per_shape[metric] = {
                                "entities": set()
                            }

                focus_node = results_graph.value(result, SH.focusNode)

                if metric and focus_node:
                    violating_entities_per_shape[metric]['entities'].add(focus_node)

                if results[metric]["message"] == "":
                    results[metric]["message"] = message

                if constraint_type != SH.MinCountConstraintComponent:
                    # shapes have ranges to check for the effective usage of properties
                    # hence, the property can be present but is not being used properly
                    message += ' (the values for the property are not correct)'

        for metric, info in violating_entities_per_shape.items():
            
            count = len(info["entities"])
            denominator = get_denominator(metric, info, self.graph_profile)

            ratio = 1 - (count / denominator)
            results[metric]["measure"] = ratio
            results[metric]['violations'] = '; '.join(info['entities'])
            results[metric]['num_violations'] = count
                
            if 'class' in info:
                results[metric]['class'] = info['class']
            elif 'property' in info:
                results[metric]['property'] = info['property']
            
        return results
    
    def create_aggregate_metric(self, metric_name, score, uri, type_, tuple_=False):
        # type_ can be 'classes' or 'properties'
        self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] += 1
        if str(score) == "1":
            self.aggregate_dict_counter[metric_name][f'{metric_name}_ones'] += 1
        else:
            if tuple_:
                self.aggregate_dict_counter[metric_name][f'{metric_name}_{type_}'].append((uri, score))
            else:
                self.aggregate_dict_counter[metric_name][f'{metric_name}_{type_}'].append(uri)

    def create_metric_info(self, metric_name, ratio, violations, num_violations, vocab=None):

        metric_dict = {
            "misplaced_properties": {
                'dimension': 'Consistency',
                'metric_id': 'CN2',
                'metric': 'No misplaced classes or properties',
                'metric_description': 'Verifies that properties aren\'t used as classes',
                'score': 0,
                'message': 'properties are used as classes',
                'metric_type': 'binary',
                'metric_calculation': "0 if property is used as a class, 1 otherwise.",
                "meta_metric_calculation": "Number of correctly used properties / Number of properties defined in vocabularies",
                'shape_name': 'MisplacedPropertiesShape',
                "shape_template": "ex:MisplacedPropertiesShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetNode PROPERTY_URI;\\n\\tsh:property [\\n\\tsh:path [sh:inversePath rdf:type];\\n\\tsh:maxCount 0;\\n\\t].",
                'violations': '',
                "violation_text": "properties used as a classes",
                'num_violations': 0,
                "vocab": ''
            },
            "misplaced_classes": {
                'dimension': 'Consistency',
                'metric_id': 'CN2',
                'metric': 'No misplaced classes or properties',
                'metric_description': 'Verifies that classes aren\'t used as properties',
                'score': 0,
                'message': 'classes are used as properties',
                'metric_type': 'binary',
                'metric_calculation': "0 if property is used as a class, 1 otherwise.",
                "meta_metric_calculation": "Number of correctly used classes / Number of classes defined in vocabularies",
                'shape_name': 'MisplacedClassesShape',
                "shape_template": "ex:MisplacedClassesShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf rdf:type;\\n\\tsh:or (\\n\\t[sh:path rdf:type; sh:hasValue rdfs:Class;]\\n\\t[sh:path rdf:type; sh:hasValue rdf:Property;]\\n\\t[sh:path rdf:type; sh:hasValue owl:NamedIndividual;]\\n\\t[\\n\\tsh:path CLASS_URI;\\n\\tsh:maxCount 0;\\n\\t]\\n\\t).",
                'violations': '',
                "violation_text": "classes used as a property",
                'num_violations': 0,
                "vocab": ''
            },
            "correct_range": {
                'dimension': 'Consistency',
                'metric_id': 'CN9',
                'metric': 'Correct domain and range definition',
                'metric_description': 'Verifies that properties are used with the correct range.',
                'score': 0,
                'message': 'are used with incorrect range',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities that use the property)',
                'meta_metric_calculation': 'Number of properties used with a correct range / Number of properties with a defined range',
                'shape_name': 'CorrectRangeShape',
                "shape_template": "ex:CorrectRangeShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:property [\\nsh:path PROPERTY_URI;\\nsh:datatype DATATYPE; % or sh:class CLASS\\n].\\n\\nex:CorrectRangeShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:property [\\nsh:path PROPERTY_URI;\\nsh:nodeKind sh:BlankNodeOrIRI;\\n].\\n\\nex:CorrectRangeShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:property [\\nsh:path PROPERTY_URI;\\nsh:nodeKind sh:Literal;\\n].\\n\\nex:CorrectRangeShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:property [\\nsh:path PROPERTY_URI;\\nsh:or (\\n[ sh:nodeKind sh:BlankNodeOrIri; ]\\n[ sh:nodeKind sh:Literal; ]\\n);\\n].",
                'violations': '',
                "violation_text": "(property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "correct_domain": {
                'dimension': 'Consistency',
                'metric_id': 'CN9',
                'metric': 'Correct domain and range definition.',
                'metric_description': 'Verifies that properties are used with the correct domain.',
                'score': 0,
                'message': 'properties are used with incorrect domains',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities that use the property)',
                "meta_metric_calculation": "Number of properties used with their correct domain / Number of properties with a defined domain",
                'shape_name': 'CorrectDomainShape',
                "shape_template": "ex:CorrectDomainShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:class CLASS.\\n\\nex:CorrectDomainShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI;\\nsh:nodeKind sh:BlankNodeOrIRI.",
                'violations': '',
                "violation_text": "(property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "entities_disjoint_classes": {
                'dimension': 'Consistency',
                'metric_id': 'CN1',
                'metric': 'No use of entities as members of disjoint classes',
                'metric_description': 'Verifies there are no entities that are members of disjoint classes.',
                'score': 0,
                'message': 'classes have instances of disjoint classes',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities of the target class)',
                "meta_metric_calculation": "Number of classes with no member as instance of a disjoint class / Number of disjoint classes",
                'shape_name': 'EntitiesDisjointClassesShape',
                "shape_template": "ex:EntitiesDisjointClassesShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetClass CLASS_URI;\\n\\tsh:not [ sh:class DISJOINT_CLASS_URI].",
                'violations': '',
                "violation_text": "(disjoint class, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "irreflexive_property": {
                'dimension': 'Consistency',
                'metric_id': 'CN10',
                'metric': 'No inconsistent values',
                'metric_description': 'Verifies the correct usage of irreflexive properties.',
                'score': 0,
                'message': 'properties don\'t conform to their irreflexive characteristic',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of subjects that use the property)',
                "meta_metric_calculation": "Number of irreflexive properties correctly used / Number of irreflexive properties",
                'shape_name': 'IrreflexivePropertyShape',
                "shape_template": "ex:IrreflexivePropertyShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf PROPERTY_URI;\\n\\tsh:disjoint PROPERTY_URI.",
                'violations': '',
                "violation_text": "(irreflexive property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "self_descriptive_format_properties": {
                "dimension": 'Interpretability',
                "metric_id": "ITP1",
                "metric": "Use of self-descriptive formats",
                'metric_description': 'Verifies if properties use IRIs as values',
                'score': 0,
                'message': 'properties use at least one literal or blank node',
                'metric_type': 'count',
                'metric_calculation': '1 if the property uses IRIs as values, 0 otherwise.',
                "meta_metric_calculation": "Number of properties that have IRIs as values / Number of properties used in the dataset",
                'shape_name': 'SelfDescriptiveFormatPropertiesShape',
                "shape_template": "ex:SelfDescriptiveFormatPropertiesShape\\na sh:NodeShape ;\\nsh:targetObjectsOf PROPERTY_URI;\\nsh:nodeKind sh:IRI.",
                'violations': '',
                "violation_text": "properties used with blank nodes or literals",
                'num_violations': 0,
                "vocab": ''
            },
            "misuse_object_properties": {
                'dimension': 'Consistency',
                'metric_id': 'CN3',
                'metric': 'No misuse of owl:DatatypeProperty or owl:ObjectProperty',
                'metric_description': 'Verifies that owl:ObjectProperty aren\'t used with Literals',
                'score': 0,
                'message': 'object properties are used with literals or blank nodes',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities that use the property)',
                "meta_metric_calculation": "Number of owl:ObjectProperty correctly used / Number of owl:ObjectProperty used in the dataset",
                'shape_name': 'MisuseOwlObjectPropertiesShape',
                "shape_template": "ex:MisuseObjectPropertiesShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf PROPERTY_URI;\\n\\tsh:property [\\n\\t\\tsh:path PROPERTY_URI;\\n\\t\\tsh:nodeKind sh:BlankNodeOrIRI;\\n\\t].",
                'violations': '',
                "violation_text": "(object property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "misuse_datatype_properties": {
                'dimension': 'Consistency',
                'metric_id': 'CN3',
                'metric': 'No misuse of owl:DatatypeProperty or owl:ObjectProperty',
                'metric_description': 'Verifies that owl:DatatypeProperty are used with Literals',
                'score': 0,
                'message': 'datatype properties are used with IRIs',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities that use the property)',
                "meta_metric_calculation": "Number of owl:DatatypeProperty correctly used / Number of owl:DatatypeProperty used in the",
                'shape_name': 'MisuseOwlDatatypePropertiesShape',
                "shape_template": "ex:MisuseDatatypePropertiesShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf PROPERTY_URI;\\n\\tsh:property [\\n\\tsh:path PROPERTY_URI;\\n\\tsh:nodeKind sh:Literal;\\n\\t].",
                'violations': ' ',
                "violation_text": "(datatype property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "functional_property": {
                'dimension': 'Consistency',
                'metric_id': 'CN10',
                'metric': 'No inconsistent values',
                'metric_description': 'Verifies the correct usage of functional properties.',
                'score': 0,
                'message': 'properties don\'t conform to their functional characteristic',
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities that use the property)',
                "meta_metric_calculation": "Number of functional properties correctly used / Number of functional properties",
                'shape_name': 'FunctionalPropertyShape',
                "shape_template": "ex:FunctionalPropertyShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf PROPERTY_URI;\\n\\tsh:property [\\n\\t\\tsh:path PROPERTY_URI;\\n\\t\\tsh:maxCount 1;\\n\\t].",
                'violations': '',
                "violation_text": "(functional property, individual score)",
                'num_violations': 0,
                "vocab": ''
            },
            "schema_completeness_class_usage": {
                    'dimension': 'Completeness',
                    'metric_id': 'CP1',
                    'metric': 'Schema completeness',
                    'metric_description': 'Verifies that classes defined in vocabularies are used in the dataset.',
                    'score': 0,
                    'message': 'classes aren\'t used in the dataset',
                    'metric_type': 'binary',
                    "metric_calculation": "1 if the class is used, 0 otherwise",
                    "meta_metric_calculation": "Number of classes used from the vocabularies / Number of classes defined in vocabularies",
                    'shape_name': 'SchemaCompletenessClassUsageShape',
                    "shape_template": "ex:NotNamedIndividualShape\\n\\ta sh:NodeShape;\\n\\tsh:property [\\n\\t\\tsh:path rdf:type ;\\n\\t\\tsh:not [ sh:hasValue owl:NamedIndividual ] ;\\n\\t].\\nex:SchemaCompletenessClassUsageShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetNode CLASS_URI ;\\n\\tsh:property [\\n\\t\\tsh:path [ sh:inversePath rdf:type ] ;\\n\\t\\tsh:minCount 1 ;\\n\\t\\tsh:qualifiedValueShape [\\n\\t\\t\\tsh:node ex:NotNamedIndividualShape ;\\n\\t\\t];\\n\\t\\tsh:qualifiedMinCount 1 ;\\n\\t].",
                    'violations': '',
                    "violation_text": "classes defined in the vocabulary that are not used in the dataset",
                    'num_violations': 0,
                    "vocab": ''
                },
            "malformed_literal": {
                "dimension": "Syntactic Validity",
                "metric_id": "SV3",
                "metric": "No malformed datatype literals",
                "score": 0,
                "message": "properties are used with malformed datatype values",
                "metric_description": "Verifies that datatype property's values follow the expected lexical syntax of the datatype or that it isn't an ill-typed literal.",
                "metric_type": "count",
                "metric_calculation": "1 - (Number of violations / Number of entities that use the property)",
                "meta_metric_calculation": "Number of correctly used properties / Number of properties with a datatype range",
                'shape_name': 'MalformedDatatypeShape',
                "shape_template": "ex:MalformedLiteralShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf PROPERTY_URI;\\n\\tsh:property [\\n\\tsh:path PROPERTY_URI ;\\n\\tsh:datatype DATATYPE_URI;\\n\\t].",
                "violations": "",
                "violation_text": "(property used with a malformed literal, individual score)",
                "num_violations": 0,
                "vocab": ''
            },
            "deprecated_property": {
                "dimension": "Consistency",
                "metric_id": "CN4",
                "metric": "Members of owl:DeprecatedClass or owl:DeprecatedProperty not used",
                "score": 0,
                "message": 'deprecated properties are used in the dataset',
                "metric_description": "Verifies that deprecated properties aren't used",
                'metric_type': 'count',
                'metric_calculation': '1 - (Number of violations / Number of entities)',
                'meta_metric_calculation': 'Number of unused deprecated properties / Number of deprecated properties',
                'shape_name': 'DeprecatedPropertiesShape',
                "shape_template": "ex:DeprecatedPropertiesUsageShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetSubjectsOf rdf:type;\\n\\tsh:or (\\n\\t\\t[sh:path rdf:type; sh:hasValue rdfs:Class;]\\n\\t\\t[sh:path rdf:type; sh:hasValue rdf:Property;]\\n\\t\\t[sh:path rdf:type; sh:hasValue owl:\\n\\t\\tNamedIndividual;]\\n\\t\\t[ sh:path PROPERTY_URI; sh:maxCount 0; ]\\n\\t).",
                'violations': '',
                "violation_text": "(deprecated property, individual score)",
                'num_violations': 0,
                'vocab': ''
            },
            "undefined_classes": {
                "dimension": "Interpretability",
                "metric_id": "ITP3",
                "metric": "Invalid usage of undefined classes and properties",
                "score": 0,
                "message": "",
                "metric_description": "Verifies that the classes used in the dataset are defined in the vocabulary.",
                "metric_type": "binary",
                "metric_calculation": "1 if the class is defined, 0 otherwise",
                "meta_metric_calculation": "Number of defined classes (from the vocabulary) used / Number of classes (from the vocabulary) used in the dataset",
                'shape_name': 'UndefinedClassShape',
                "shape_template": "ex:UndefinedClassShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetNode CLASS_URI;\\n\\tsh:property [\\n\\t\\tsh:path rdf:type;\\n\\t\\tsh:hasValue rdfs:Class;\\n\\t\\tsh:minCount 1;\\n\\t].",
                "violations": "",
                "violation_text": "undefined classes",
                "num_violations": 0,
                "vocab": ''
            },
            "undefined_properties": {
                "dimension": "Interpretability",
                "metric_id": "ITP3",
                "metric": "Invalid usage of undefined classes and properties",
                "score": 0,
                "message": "",
                "metric_description": "Verifies that the properties used in the dataset are defined in the vocabulary.",
                "metric_type": "binary",
                "metric_calculation": "1 if the property is defined, 0 otherwise",
                "meta_metric_calculation": "Number of defined properties (from the vocabulary) used / Number of properties (from the vocabulary) used in the dataset",
                'shape_name': 'UndefinedPropertyShape',
                "shape_template": "ex:UndefinedPropertyShape\\n\\ta sh:NodeShape ;\\n\\tsh:targetNode PROPERTY_URI;\\n\\tsh:property [\\n\\t\\tsh:path rdf:type;\\n\\t\\tsh:hasValue rdf:Property;\\n\\t\\tsh:minCount 1;\\n\\t].",
                "violations": "",
                "violation_text": "undefined properties",
                "num_violations": 0,
                "vocab": ''
            }

        }

        metric_dict[metric_name]["score"] = ratio
        
        if ratio < 1 and not vocab:
            param_shapes = f'count_{metric_name}_shapes'
            param_ones = f'{metric_name}_ones'
            metric_dict[metric_name]["message"] = f'{self.aggregate_dict_counter[metric_name][param_shapes] - self.aggregate_dict_counter[metric_name][param_ones]} ' + metric_dict[metric_name]["message"]
        else:
            metric_dict[metric_name]["message"] = ''

        metric_dict[metric_name]["violations"] = violations
        metric_dict[metric_name]["num_violations"] = num_violations

        if vocab:
            metric_dict[metric_name]["vocab"] = vocab

        return metric_dict[metric_name]

        
    def create_dq_results_csv(self):

        """
        Create a CSV with columns: 'dimension', 'metric', 'metric_id', 'metric_description', 'score', 'message', 'metric_type', 'metric_calculation', 'meta_metric_calculation', 'shape_template', 'violations'
        from DQ assessment JSON files.
        """
        results_folder = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)

        files = []
        if self.validate_metadata_shapes: 
            files.append(f'dq_assessment_{self.dataset_name}_metadata.json')
        
        if self.validate_data_shapes: 
            files.append(f'dq_assessment_{self.dataset_name}_data.json')

        if self.validate_vocabulary_shapes:
            vocab_files = [file.split("/")[-1] for file in glob.glob(f'{results_folder}dq_assessment_vocabularies_*.json')]
            files.extend(vocab_files)

        rows = []
        counter_shapes = 0

        for filename in files:

            file_path = os.path.join(results_folder, filename)
            
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.aggregate_dict_counter = {
                "misplaced_properties": {
                    "misplaced_properties_ones": 0,
                    "count_misplaced_properties_shapes": 0,
                    "misplaced_properties_properties": []
                },
                "misplaced_classes": {
                    "misplaced_classes_ones": 0,
                    "count_misplaced_classes_shapes": 0,
                    "misplaced_classes_classes": []
                },
                "correct_range": {
                    "correct_range_ones": 0,
                    "count_correct_range_shapes": 0,
                    "correct_range_properties": []
                },
                "correct_domain": {
                    "correct_domain_ones": 0,
                    "count_correct_domain_shapes": 0,
                    "correct_domain_properties": []
                },
                "entities_disjoint_classes": {
                    "entities_disjoint_classes_ones": 0,
                    "count_entities_disjoint_classes_shapes": 0,
                    "entities_disjoint_classes_classes": []
                },
                "misuse_datatype_properties": {
                    "misuse_datatype_properties_ones": 0,
                    "count_misuse_datatype_properties_shapes": 0,
                    "misuse_datatype_properties_properties": []
                },
                "misuse_object_properties": {
                    "misuse_object_properties_ones": 0,
                    "count_misuse_object_properties_shapes": 0,
                    "misuse_object_properties_properties": []
                },
                "irreflexive_property": {
                    "irreflexive_property_ones": 0,
                    "count_irreflexive_property_shapes": 0,
                    "irreflexive_property_properties": []
                },
                "self_descriptive_format_properties": {
                    "self_descriptive_format_properties_ones": 0,
                    "count_self_descriptive_format_properties_shapes": 0,
                    "self_descriptive_format_properties_properties": []
                },
                "functional_property": {
                    "functional_property_ones": 0,
                    "count_functional_property_shapes": 0,
                    "functional_property_properties": []
                },
                "schema_completeness_class_usage": {
                    "schema_completeness_class_usage_ones": 0,
                    "count_schema_completeness_class_usage_shapes": 0,
                    "schema_completeness_class_usage_classes": []
                },
                "malformed_literal": {
                    "malformed_literal_ones": 0,
                    "count_malformed_literal_shapes": 0,
                    "malformed_literal_properties": []
                },
                "undefined_classes": {
                    "undefined_classes_ones": {},
                    "count_undefined_classes_shapes": {},
                    "undefined_classes_classes": {}
                },
                "undefined_properties": {
                    "undefined_properties_ones": {},
                    "count_undefined_properties_shapes": {},
                    "undefined_properties_properties": {}
                },
                "deprecated_property": {
                    "deprecated_property_ones": 0,
                    "count_deprecated_property_shapes": 0,
                    "deprecated_property_properties": []
                }
            }

            for shape_name, info in data.items():
                counter_shapes += 1
                
                if not isinstance(info, dict):
                    continue

                dimension = info.get('dimension', '')
                score = info.get('measure', '')
                description = info.get('description', '')
                message = info.get('message', '')
                metric_name = info.get('metric', '')
                metric_id = info.get('metric_id', '')
                metric_type = info.get('metric_type', '')
                metric_calculation = info.get('metric_calculation', '')
                meta_metric_calculation = info.get('meta_metric_calculation', '')
                shape_template = info.get('shape_template', '')
                num_violations = info.get('num_violations', 0)
                violations = info.get('violations', '')
                violation_text = info.get('violation_text', '')
                class_uri = info.get('class', '')
                property_uri = info.get('property', '')
                vocab = info.get('vocab', '')

                if shape_name.startswith("MisplacedProp"):
                    # this counts the number of properties, since I create 1 shape 
                    # per property and in the results I have a result per shape
                    self.create_aggregate_metric("misplaced_properties", score, property_uri, type_="properties", tuple_=False)

                elif shape_name.startswith("MisplacedClasses"):

                    # this counts the number of classes, since I create 1 shape 
                    # per class and in the results I have a result per shape
                    self.create_aggregate_metric("misplaced_classes", score, class_uri, type_='classes', tuple_=False)
                
                elif shape_name.startswith("CorrectRange_"):
                    self.create_aggregate_metric("correct_range", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("CorrectDomain_"):
                    self.create_aggregate_metric("correct_domain", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("EntitiesDisjointClasses_"):
                    self.aggregate_dict_counter['entities_disjoint_classes']['count_entities_disjoint_classes_shapes'] += 2
                    if str(score) == "1":
                        self.aggregate_dict_counter['entities_disjoint_classes']['entities_disjoint_classes_ones'] += 2 # is this ok?????
                    else:
                        self.aggregate_dict_counter['entities_disjoint_classes']['entities_disjoint_classes_classes'].append((class_uri['first_class'], class_uri['second_class'], score))
                
                elif shape_name.startswith("MisuseOwlObjectProperties_"):
                    # Count the number of properties that are used correctly (there's no triple that uses them incorrectly) 
                    # over total number of owl object properties
                    self.create_aggregate_metric("misuse_object_properties", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("MisuseOwlDatatypeProperties_"):
                    self.create_aggregate_metric("misuse_datatype_properties", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("IrreflexiveProperty_"):
                    self.create_aggregate_metric("irreflexive_property", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("SelfDescriptiveFormatProperties"):
                    self.create_aggregate_metric("self_descriptive_format_properties", score, property_uri, type_="properties", tuple_=False)

                elif shape_name.startswith("FunctionalProperty"):
                    self.create_aggregate_metric("functional_property", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("SchemaCompletenessClassUsage"):
                    self.create_aggregate_metric("schema_completeness_class_usage", score, class_uri, type_='classes', tuple_=False)

                elif shape_name.startswith("MalformedLiteral"):
                    # 1 shape per property, so this counts the number of properties
                    self.create_aggregate_metric("malformed_literal", score, property_uri, type_="properties", tuple_=True)
                
                elif shape_name.startswith("DeprecatedProperties"):
                    # 1 shape per property, so this counts the number of properties
                    self.create_aggregate_metric("deprecated_property", score, property_uri, type_="properties", tuple_=True)

                elif shape_name.startswith("UndefinedClass"):
                    metric_name = "undefined_classes"
                    if vocab not in self.aggregate_dict_counter[metric_name]['count_undefined_classes_shapes'].keys():
                        self.aggregate_dict_counter[metric_name]['count_undefined_classes_shapes'][vocab] = 0
                        self.aggregate_dict_counter[metric_name]['undefined_classes_ones'][vocab] = 0
                        self.aggregate_dict_counter[metric_name]['undefined_classes_classes'][vocab] = []

                    self.aggregate_dict_counter[metric_name]['count_undefined_classes_shapes'][vocab] += 1
                    if str(score) == '1':
                        self.aggregate_dict_counter[metric_name]['undefined_classes_ones'][vocab] += 1
                    else:
                        self.aggregate_dict_counter[metric_name]['undefined_classes_classes'][vocab].append(class_uri)

                elif shape_name.startswith("UndefinedProperty"):
                    metric_name = "undefined_properties"
                    if vocab not in self.aggregate_dict_counter[metric_name]['count_undefined_properties_shapes'].keys():
                        self.aggregate_dict_counter[metric_name]['count_undefined_properties_shapes'][vocab] = 0
                        self.aggregate_dict_counter[metric_name]['undefined_properties_ones'][vocab] = 0
                        self.aggregate_dict_counter[metric_name]['undefined_properties_properties'][vocab] = []

                    self.aggregate_dict_counter[metric_name]['count_undefined_properties_shapes'][vocab] += 1
                    if str(score) == '1':
                        self.aggregate_dict_counter[metric_name]['undefined_properties_ones'][vocab] += 1
                    else:
                        self.aggregate_dict_counter[metric_name]['undefined_properties_properties'][vocab].append(property_uri)

                else:

                    if shape_name.startswith("DeprecatedClasses"):
                        num_violations = len([v for v in violations.split(";") if v.strip()])
                    
                    # violations contains the values of the property that are used multiple times
                    if shape_name.startswith("InverseFunctionalPropertyUniqueness"):
                        value_violations = [v.strip() for v in violations.split(";")]
                        num_violations = len(value_violations)
                        
                        if len(value_violations) > 0:
                            violations = f'({property_uri}); ' + violations + ' )'

                    rows.append({
                        'dimension': dimension,
                        'metric': metric_name,
                        'metric_id': metric_id,
                        'metric_description': description,
                        'score': score,
                        'message': message,
                        'metric_type': metric_type,
                        'metric_calculation': metric_calculation,
                        'meta_metric_calculation': meta_metric_calculation,
                        'shape_name': shape_name,
                        'shape_template': shape_template,
                        'violations': violations,
                        'violation_text': violation_text,
                        'num_violations': num_violations,
                        'vocab': vocab
                    })

            # Misuse properties
            metric_name = "misplaced_properties"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                # I create a shape for each property and from the validation result
                # I save the score 1 or 0 for each shape 

                # misplaced_properties_ones : counts the number of properties correctly used
                # count_misplaced_properties_shapes : counts the number of properties (shapes)
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
                
            metric_name = "misplaced_classes"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:

                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
                
            # Correct range object
            metric_name = "correct_range"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Correct domain
            metric_name = "correct_domain"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Entities in disjoint classes
            metric_name = "entities_disjoint_classes"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({fc},{sc},{s})' for fc, sc, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_classes']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Irreflexive properties
            metric_name = "irreflexive_property"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
            
            # Self descriptive formats properties
            metric_name = "self_descriptive_format_properties"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Misuse object properties
            metric_name = "misuse_object_properties"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Misuse datatype properties
            metric_name = "misuse_datatype_properties"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Functional properties
            metric_name = "functional_property"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))

            # Schema completeness class usage
            metric_name = "schema_completeness_class_usage"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
                
            metric_name = "malformed_literal"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
            
            metric_name = "undefined_properties"
            if len(self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'].keys()) > 0:
                for vocab in self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'].keys():
                    ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones'][vocab] / self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'][vocab])
                    violations = "; ".join(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'][vocab])
                    num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'][vocab])
                    rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations, vocab=vocab))
            
            metric_name = "undefined_classes"
            if len(self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'].keys()) > 0:
                for vocab in self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'].keys():
                    ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones'][vocab] / self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'][vocab])
                    violations = "; ".join(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'][vocab])
                    num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_classes'][vocab])
                    rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations, vocab=vocab))

            metric_name = "deprecated_property"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                ratio = (self.aggregate_dict_counter[metric_name][f'{metric_name}_ones']/self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'])
                violations = '; '.join([f'({p},{s})' for p, s in self.aggregate_dict_counter[metric_name][f'{metric_name}_properties']])
                num_violations = len(self.aggregate_dict_counter[metric_name][f'{metric_name}_properties'])
                rows.append(self.create_metric_info(metric_name, ratio, violations, num_violations))
                    

            # this shape is instantiated for every property used in the dataset that
            # has a domain defined
            metric_name = "correct_domain"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                self.graph_profile['num_properties_domain'] = self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes']

            # this shape is instantiated for every property defined in all vocabs
            metric_name = "misplaced_properties"
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                self.graph_profile['num_properties_vocabularies'] = self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes']

            # this shapes is instantiated for every class defined in the vocab
            metric_name = 'schema_completeness_class_usage'
            if self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes'] > 0:
                self.graph_profile['num_classes_vocabularies'] = self.aggregate_dict_counter[metric_name][f'count_{metric_name}_shapes']

        output_csv_path = f'{results_folder}/dq_assessment_{self.dataset_name}.csv'

        with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['dimension','metric_id', 'metric', 
                                                         'score', 'message', 'metric_description', 'metric_type', 
                                                         'metric_calculation', 'meta_metric_calculation', 'shape_name', 'shape_template',
                                                         'violations', 'violation_text', 'num_violations', 'vocab'])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        self.counter_shapes = counter_shapes
