import configparser
import logging
import csv
from jinja2 import Environment, FileSystemLoader
import time
import glob

from shacl_shape_builder import SHACLShapeBuilder
from utils import *

logging.basicConfig(level=logging.INFO)

class DQAssessment:

    def __init__(self, config_path, 
                 metadata_shapes=True, 
                 data_shapes=True, 
                 inference_data_shapes=True, 
                 vocab_shapes=True):
        
        self.metadata_shapes = metadata_shapes
        self.data_shapes = data_shapes
        self.inference_data_shapes = inference_data_shapes
        self.config = self._load_config(config_path)
        self.vocab_shapes = vocab_shapes
        self._init_paths_and_params()

        self.shape_builder = SHACLShapeBuilder(self)
        
        self.counter_shapes = 0
        self.total_elapsed_time = 0
        self.data_shapes_elapsed_time = 0
        self.vocab_shapes_elapsed_time = 0
        self.metadata_shapes_elapsed_time = 0
        self.inference_shapes_elapsed_time = 0
        self.graph_profile = None

    def _load_config(self, path):
        config = configparser.ConfigParser()
        config.read(path)
        return config

    def _init_paths_and_params(self):
        
        self.graph_file_path = self.config['settings']['graph_file']
        self.vocab_names = [v.strip() for v in self.config["settings"]["vocabularies"].split(",")]

        self.graph_file_path = self.config['settings']['graph_file']
        self.graph_file_format = self.config['settings']['graph_file_format']
        self.dataset_name = self.config["settings"]["dataset_name"]
        self.dataset_name = self.dataset_name.lower().replace(" ", "_")

        self.metadata_file = self.config['settings']['metadata_file']
        self.metadata_file_format = self.config['settings']['metadata_file_format']

        # Parameters for SHACL shapes
        self.type_property = self.config['settings']['type_property']
        self.labeling_property = self.config['settings']['labeling_property']
        self.description_property = self.config['settings']['description_property']
        self.interlinking_property = self.config['settings']['interlinking_property']
        self.base_namespace = self.config['settings']['base_namespace'] # this is not being used!!!!! I think I didn't implement the shape that checks for the uriSpace...
        self.uris_max_length = self.config['settings']['uris_max_length']
        self.vocab_names = [v.strip() for v in self.config["settings"]["vocabularies"].split(",")]

        # Shapes templates
        env = Environment(loader=FileSystemLoader("dq_assessment/shapes"))
        self.data_template = env.get_template("data_shapes.template.ttl")
        self.metadata_template = env.get_template("metadata_shapes.template.ttl")
        self.vocabs_template = env.get_template("vocabulary_shapes.template.ttl")

        self.regex_pattern = None


    def run(self):

        self.profile_data()
        logging.info(f"Finished profiling graph and vocabularies. Saved results in {PROFILE_DATASETS_FOLDER_PATH} & {PROFILE_VOCABULARIES_FOLDER_PATH}")
        
        initial_time = time.time() # start of validation
        
        # ---- Validate shapes against vocabularies ----
        if self.vocab_shapes:
            start_time = time.time()
            self.validate_vocabulary_shapes()
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.vocab_shapes_elapsed_time = elapsed_time
            # TODO: see this
            # logging.info(f"Finished validating shapes against vocabularies. Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}dq_assessment_{self.dataset_name}_data_inference.json'. \n Elapsed time: {elapsed_time}")

        # ---- Validate metadata shapes ----
        if self.metadata_shapes and self.metadata_file:
            start_time = time.time()
            self.validate_metadata_shapes()
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.metadata_shapes_elapsed_time = elapsed_time
            logging.info(f"Finished validating metadata shapes. \n Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}dq_assessment_{self.dataset_name}_metadata.json'. \n Elapsed time: {elapsed_time}")

        # ---- Validate data shapes ----
        if self.data_shapes:
            start_time = time.time()
            self.validate_data_shapes()
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.data_shapes_elapsed_time = elapsed_time
            logging.info(f"Finished validating data shapes. Saved DQA results in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}/dq_assessment_{self.dataset_name}_data.json'. \n Elapsed time: {elapsed_time}")


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
        graph_profile_output_path = f'{PROFILE_DATASETS_FOLDER_PATH}/{self.dataset_name}.json'
        self.graph_profile = profile_graph(self, graph_profile_output_path)
        logging.info(f"Graph profile saved in {graph_profile_output_path}.")

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

        # Generate metadata shapes
        shape_graph = create_shape_graph(self.metadata_template.module.metadata_shape())

        # Save shapes
        folder_path = f'{DATASETS_FOLDER_PATH}/{self.dataset_name}/shapes'
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/metadata_shapes.ttl'
        shape_graph.serialize(destination=file_path, format='turtle')
        logging.info(f'Metadata shapes for dataset {self.dataset_name} saved in {file_path}')
        
        # Run validation 
        _, val_graph, _ = validate_shacl_constraints(self.metadata_file, self.metadata_file_format, shape_graph)

        # Process & store validation results
        self.process_validation_result_metadata(val_graph)
        
        logging.info(f"Finished DQA for metadata file. Results saved in '{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)}/dq_assessment_{self.dataset_name}_metadata.json'. \n")


    def validate_vocabulary_shapes(self):

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
            _, val_graph, _ = validate_shacl_constraints(file_path, file_format, shape_graph)

            with open(f'{PROFILE_VOCABULARIES_FOLDER_PATH}/{vocab_name}.json', 'r', encoding='utf-8') as f:
                vocab_profile = json.load(f)

            # Process validation results
            self.process_validation_result_vocabularies(val_graph, vocab_name, vocab_profile, property_vocab_map, class_vocab_map)


    def validate_data_shapes(self):
        """
            Validates shapes without inference
        """

        # Instantiate shapes
        accessibility_shapes = self.shape_builder.accessibility_data_shapes(self.data_template)
        self.regex_pattern, contextual_shapes = self.shape_builder.contextual_data_shapes(self.data_template)
        representational_shapes = self.shape_builder.representational_data_shapes(self.data_template)
        
        # Update graph_profile because it gets updated inside intrinsic_data_shapes
        intrinsic_shapes, self.graph_profile, self.shape_property_map, self.shape_class_map = self.shape_builder.intrinsic_data_shapes(self.data_template, self.graph_profile)

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

        _, val_graph, _ = validate_shacl_constraints(self.graph_file_path, self.graph_file_format, shape_graph, self.vocab_names, self.config)
        
        # Process validation results
        results = self.process_validation_result_data(val_graph)
        
        # Store dq assessment results
        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        os.makedirs(folder_path, exist_ok=True)
        file_path = f'{folder_path}/dq_assessment_{self.dataset_name}_data.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)

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
            results[metric]["measure"] = 0
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
            print('no validation result')
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
                if vocab in property_vocab_map and focus_node in property_vocab_map[vocab]:
                    results[metric]["property"] = focus_node
              
            elif metric.startswith("UndefinedClass"):
                metric = f'{metric}_{counter}'
                # check that the class is actually from the vocabulary
                if focus_node in class_vocab_map[vocab]:
                    results[metric]["class"] = focus_node
                
            elif metric and focus_node:
                # consider unique focus nodes for each metric
                if metric not in violating_entities_per_shape:
                    violating_entities_per_shape[metric] = set()
                
                # check that the class/property is actually from the vocabulary
                if (vocab in property_vocab_map and focus_node in property_vocab_map[vocab]) or (focus_node in class_vocab_map and focus_node in class_vocab_map[vocab]):
                    violating_entities_per_shape[metric].add(focus_node)

            if results[metric]["message"] == "":
                results[metric]["message"] = message
        
        for metric, nodes in violating_entities_per_shape.items():
            count = len(nodes)
            if metric == 'LabelForClasses':
                denominator = vocab_profile.get("num_classes", 1)
            elif metric == 'LabelForProperties':
                denominator = vocab_profile.get("num_properties", 1)
            
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
        
        if os.path.exists(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH):
            with open(DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
                metrics_specific = json.load(f)

        results = metrics_generic | metrics_specific

        if self.regex_pattern is None:
            # There's no regex pattern provided for the URIs, 
            # hence, we don't need to calculate the URIRegexComplianceEntities, URIRegexComplianceClasses, URIRegexComplianceProperties
            results.pop("URIRegexComplianceEntities")
        
        if not self.labeling_property:
            results.pop('DifferentLanguagesLabelsEntities')

        if not self.description_property:
            results.pop('DifferentLanguagesDescriptionsEntities')

        validation_results = results_graph.subjects(RDF.type, SH.ValidationResult)
        if not any(validation_results):
            print("No validation results found.")
            return results

        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            
            constraint_type = results_graph.value(result, SH.sourceConstraintComponent)
            metric, message, counter = get_metric_message(results_graph, result)

            if metric in BINARY_METRICS_DATA:
                
                if counter != -1 and not metric.startswith("Deprecated"):
                    metric = f'{metric}_{counter}'

                if constraint_type != SH.MinCountConstraintComponent and metric != 'MisplacedProperties':
                    # shapes have ranges to check for the effective usage of properties
                    # hence, the property can be present but is not being used properly
                    message += ' (the values for the property are not correct)'
                
                if metric.startswith("MisplacedProperties"):
                    results[metric]["property"] = self.shape_property_map[int(counter)]
              
                if metric.startswith("SchemaCompletenessClassUsage"):
                    results[metric]["class"] = self.shape_class_map[int(counter)]
                
                if metric.startswith("DeprecatedClasses"):
                    if "violations" not in results[metric]:
                        results[metric]['violations'] = ''

                    focus_node = results_graph.value(result, SH.focusNode)
                    results[metric]['violations'] += ';' + focus_node
                
                if metric.startswith("DeprecatedProperties"):
                    if "violations" not in results[metric]:
                        results[metric]['violations'] = ''

                    focus_node = results_graph.value(result, SH.focusNode)
                    results[metric]['violations'] += ';' + focus_node

                results[metric]["measure"] = 0 
            
            elif metric in COUNT_METRICS:
            
                if metric in NUM_TRIPLES_PER_PROPERTY:
                    
                    if counter != -1:
                        metric = f'{metric}_{counter}'
                    if metric not in violating_entities_per_shape:

                        violating_entities_per_shape[metric] = {
                            "entities": set(),
                            "property": self.shape_property_map[int(counter)]
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
                    if metric not in violating_entities_per_shape:
                        if counter != -1:
                            metric = f'{metric}_{counter}'
                        violating_entities_per_shape[metric] = {
                            "entities": set()
                        }

                focus_node = results_graph.value(result, SH.focusNode)
                if metric and focus_node:
                    # consider unique focus nodes for each metric
                    violating_entities_per_shape[metric]['entities'].add(focus_node)

            if results[metric]["message"] == "":
                results[metric]["message"] = message

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


    def create_dq_results_csv(self):

        """
        Create a CSV with columns: 'dimension', 'metric', 'metric_id', 'metric_description', 'score', 'message', 'metric_type', 'metric_calculation', 'meta_metric_calculation', 'shape_template', 'inference', 'violations'
        from DQ assessment JSON files.
        """
        results_folder = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)

        files = []
        if self.validate_metadata_shapes: 
            files.append(f'dq_assessment_{self.dataset_name}_metadata.json')

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
            
            # misuse properties
            misuse_properties_ones = 0
            count_misuse_properties_shapes = 0
            misuse_properties_properties = []

            # correct range datatype
            correct_range_datatype_ones = 0
            count_correct_range_datatype_shapes = 0
            range_datatype_properties = []
            
            # correct range object
            correct_range_object_ones = 0
            count_correct_range_object_shapes = 0
            range_object_properties = []

            # correct domain
            correct_domain_ones = 0
            count_correct_domain_shapes = 0
            correct_domain_properties = []

            # correct entities disjoint classes
            count_entities_disjoint_classes_shapes = 0
            entities_disjoint_classes_ones = 0
            entities_disjoint_classes = []

            # misuse datatype properties
            misuse_datatype_properties_ones = 0
            count_datatype_misuse_properties_shapes = 0
            misuse_datatype_properties_properties = []

            # misuse object properties
            misuse_object_properties_ones = 0
            count_object_misuse_properties_shapes = 0
            misuse_object_properties_properties = []

            # irreflexive property
            irreflexive_property_ones = 0
            count_irreflexive_properties_shapes = 0
            irreflexive_properties_properties = []

            # inverse functional property
            inverse_functional_property_ones = 0
            count_inverse_functional_properties_shapes = 0
            inverse_functional_properties_properties = []

            # functional property
            functional_property_ones = 0
            count_functional_properties_shapes = 0
            functional_properties_properties = []

            # schema completeness class
            schema_completeness_class_usage_ones = 0
            count_schema_completeness_class_usage_shapes = 0
            schema_completeness_class_usage_classes = []

            # malformed datatype
            count_malformed_dataype_shapes = 0
            malformed_dataype_ones = 0
            malformed_dataype_properties = []

            # incompatible datatype
            count_incompatible_dataype_shapes = 0
            incompatible_dataype_ones = 0
            incompatible_dataype_properties = []

            # undefined classes
            count_undefined_classes_shapes = {}
            undefined_classes_ones = {}
            undefined_classes_classes = {}

            # undefined properties
            count_undefined_properties_shapes = {}
            undefined_properties_ones = {}
            undefined_properties_properties = {}

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
                meta_metric_calculation = info.get('metric_meta_calculation', '')
                shape_template = info.get('shape_template', '')
                num_violations = info.get('num_violations', 0)
                violations = info.get('violations', '')
                class_uri = info.get('class', '')
                property_uri = info.get('property', '')
                vocab = info.get('vocab', '')

                if shape_name.startswith("MisplacedProperties_"):

                    # this counts the number of properties, since I create 1 shape 
                    # per property and in the results I have a result per shape
                    count_misuse_properties_shapes += 1 
                    if str(score) == "1":
                        misuse_properties_ones += 1
                    else:
                        misuse_properties_properties.append((property_uri, score))

                elif shape_name.startswith("CorrectRangeDatatype_"):
                    count_correct_range_datatype_shapes += 1
                    if str(score) == "1":
                        correct_range_datatype_ones += 1
                    else:
                        range_datatype_properties.append((property_uri, score))

                elif shape_name.startswith("CorrectRangeObject_"):
                    count_correct_range_object_shapes += 1
                    if str(score) == "1":
                        correct_range_object_ones += 1
                    else:
                        range_object_properties.append((property_uri, score))

                elif shape_name.startswith("CorrectDomain_"):
                    count_correct_domain_shapes += 1
                    if str(score) == "1":
                        correct_domain_ones += 1
                    else:
                        correct_domain_properties.append((property_uri, score))

                elif shape_name.startswith("EntitiesDisjointClasses_"):
                    count_entities_disjoint_classes_shapes += 1
                    if str(score) == "1":
                        entities_disjoint_classes_ones += 1
                    else:
                        entities_disjoint_classes.append((class_uri['first_class'], class_uri['second_class'], score))
                
                elif shape_name.startswith("MisuseOwlObjectProperties_"):
                    # Count the number of properties that are used correctly (there's no triple that uses them incorrectly) 
                    # over total number of owl object properties
                    count_object_misuse_properties_shapes += 1
                    if str(score) == "1":
                        misuse_object_properties_ones += 1
                    else:
                        misuse_object_properties_properties.append((property_uri, score))

                elif shape_name.startswith("MisuseOwlDatatypeProperties_"):
                    count_datatype_misuse_properties_shapes += 1
                    if str(score) == "1":
                        misuse_datatype_properties_ones += 1
                    else:   
                        misuse_datatype_properties_properties.append((property_uri, score))

                elif shape_name.startswith("IrreflexiveProperty_"):
                    count_irreflexive_properties_shapes += 1
                    if str(score) == "1":
                        irreflexive_property_ones += 1
                    else:   
                        irreflexive_properties_properties.append((property_uri, score))

                elif shape_name.startswith("InverseFunctionalProperty_"):
                    count_inverse_functional_properties_shapes += 1
                    if str(score) == "1":
                        inverse_functional_property_ones += 1
                    else:   
                        inverse_functional_properties_properties.append((property_uri, score))

                elif shape_name.startswith("SchemaCompletenessClassUsage_"):

                    # 1 shape per class, so this counts the number of classes
                    count_schema_completeness_class_usage_shapes += 1
                    if str(score) == "1":
                        # The metric is binary, so this returns the number of classes used
                        schema_completeness_class_usage_ones += 1
                    else:   
                        schema_completeness_class_usage_classes.append(class_uri)

                elif shape_name.startswith("DeprecatedClasses"):
                    count_violations = len([v for v in violations.split("; ") if v.strip()])
                    score = 1 - ( count_violations / profile_graph['count_deprecated_classes'])

                elif shape_name.startswith("DeprecatedProperties"):
                    count_violations = len([v for v in violations.split("; ") if v.strip()])
                    score = 1 - ( count_violations / profile_graph['count_deprecated_properties'])

                elif shape_name.startswith("MalformedDatatype"):
                    # 1 shape per property, so this counts the number of properties
                    count_malformed_dataype_shapes += 1
                    if str(score) == "1":
                        # The metric is count, so this returns the number of properties that
                        # are correctly used
                        malformed_dataype_ones += 1
                    else:   
                        malformed_dataype_properties.append((property_uri, score))

                elif shape_name.startswith("MemberIncompatibleDatatype"):
                    # 1 shape per property, so this counts the number of properties
                    count_incompatible_dataype_shapes += 1
                    if str(score) == "1":
                        # The metric is count, so this returns the number of properties that
                        # are correctly used
                        incompatible_dataype_ones += 1
                    else:   
                        incompatible_dataype_properties.append((property_uri, score))

                elif shape_name.startswith("UndefinedClass"):
                    if vocab not in count_undefined_classes_shapes.keys():
                        count_undefined_classes_shapes[vocab] = 0
                        undefined_classes_ones[vocab] = 0
                        undefined_classes_classes[vocab] = []

                    count_undefined_classes_shapes[vocab] += 1
                    if str(score) == '1':
                        undefined_classes_ones[vocab] += 1
                    else:
                        undefined_classes_classes[vocab].append(class_uri)

                elif shape_name.startswith("UndefinedProperty"):
                    if vocab not in count_undefined_properties_shapes.keys():
                        count_undefined_properties_shapes[vocab] = 0
                        undefined_properties_ones[vocab] = 0
                        undefined_properties_properties[vocab] = []

                    count_undefined_properties_shapes[vocab] += 1
                    if str(score) == '1':
                        undefined_properties_ones[vocab] += 1
                    else:
                        undefined_properties_properties[vocab].append(property_uri)
                
                else:
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
                        'shape_template': shape_template,
                        'violations': violations,
                        'num_violations': num_violations,
                        'vocab': vocab
                    })

            # Misuse properties
            if count_misuse_properties_shapes > 0:
                # I create a shape for each property and from the validation result
                # I save the score 1 or 0 for each shape 

                # misuse_properties_ones : counts the number of properties correctly used
                # count_misuse_properties_shapes : counts the number of properties (shapes)
                ratio = (misuse_properties_ones/count_misuse_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN2',
                    'metric': 'No misplaced classes or properties',
                    'metric_description': 'Verifies that properties aren\'t used as classes',
                    'score': ratio,
                    'message': f'{(count_misuse_properties_shapes - misuse_properties_ones)} properties are used as classes' if ratio < 1 else '',
                    'metric_type': 'binary',
                    'metric_calculation': "0 if property is used as a class, 1 otherwise.",
                    "meta_metric_calculation": "Number of correctly used properties / Number of properties defined in vocabularies",
                    'shape_template': 'ex:MisplacedPropertiesShape\na sh:NodeShape ;\nsh:targetNode PROPERTY_URI ;\nsh:property [\nsh:path [ sh:inversePath rdf:type ];\nsh:maxCount 0;\n].',
                    'violations': '; '.join([f'({p},{s})' for p, s in misuse_properties_properties]),
                    'num_violations': len(misuse_properties_properties),
                    "vocab": ''
                })
            
            # Correct range datatype
            if count_correct_range_datatype_shapes > 0:
                ratio = (correct_range_datatype_ones/count_correct_range_datatype_shapes)
                number_violations = count_correct_range_datatype_shapes - correct_range_datatype_ones
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN9',
                    'metric': 'Correct domain and range definition',
                    'metric_description': 'Verifies that properties are used with the correct range (datatype properties).',
                    'score': ratio,
                    'message': f'{number_violations} {'properties' if number_violations > 1 else 'property'} are used with incorrect range' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    'meta_metric_calculation': 'Number of properties used with a correct datatype/literal  range / Number of properties with datatype/literal range',
                    'shape_template': 'ex:CorrectRangeShape\na sh:NodeShape ;\nsh:targetObjectsOf PROPERTY_URI ;\nsh:datatype DATATYPE.',
                    'violations': '; '.join([f'({p},{s})' for p, s in range_datatype_properties]),
                    'num_violations': len(range_datatype_properties),
                    "vocab": ''
                })

            # Correct range object
            if count_correct_range_object_shapes > 0:
                ratio = (correct_range_object_ones/count_correct_range_object_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN9',
                    'metric': 'Correct domain and range definition.',
                    'metric_description': 'Verifies that properties are used with the correct range (object properties).',
                    'score': ratio,
                    'message': f'{count_correct_range_object_shapes - correct_range_object_ones} properties are used with incorrect ranges' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of properties used with an correct object range / Number of properties with object range",
                    'shape_template': 'ex:CorrectRangeObjectShape\na sh:NodeShape ;\nsh:targetObjectsOf PROPERTY_URI ;\nsh:class CLASS.',
                    'violations': '; '.join([f'({p},{s})' for p, s in range_object_properties]),
                    'num_violations': len(range_object_properties),
                    "vocab": ''
                })

            # Correct domain
            if count_correct_domain_shapes > 0:
                ratio = (correct_domain_ones/count_correct_domain_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN9',
                    'metric': 'Correct domain and range definition.',
                    'metric_description': 'Verifies that properties are used with the correct domain.',
                    'score': ratio,
                    'message': f'{count_correct_domain_shapes - correct_domain_ones} properties are used with incorrect domains' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of properties used with their correct domain / Number of properties with a defined domain",
                    "shape_template": "ex:CorrectDomainShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI ;\\nsh:class CLASS .",
                    'violations': '; '.join([f'({p},{s})' for p, s in correct_domain_properties]),
                    'num_violations': len(correct_domain_properties),
                    "vocab": ''
                })

            # Entities in disjoint classes
            if count_entities_disjoint_classes_shapes > 0:
                ratio = (entities_disjoint_classes_ones/count_entities_disjoint_classes_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN1',
                    'metric': 'No use of entities as members of disjoint classes',
                    'metric_description': 'Verifies there are no entities that are members of disjoint classes.',
                    'score': ratio,
                    'message': f'{count_entities_disjoint_classes_shapes - entities_disjoint_classes_ones} classes have instances of disjoint classes' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of entities of the target class)',
                    "meta_metric_calculation": "Number of classes with no member as instance of a disjoint class / Number of classes",
                    'shape_template': 'ex:EntitiesDisjointClassesShape\na sh:NodeShape ;\nsh:targetClass CLASS_URI ;\nsh:not [ sh:class ex:DisjointClass ].',
                    'violations': '; '.join([f'({fc},{sc},{s})' for fc, sc, s in entities_disjoint_classes]),
                    'num_violations': len(entities_disjoint_classes),
                    "vocab": ''
                })

            # Irreflexive properties
            if count_irreflexive_properties_shapes > 0:
                ratio = (irreflexive_property_ones/count_irreflexive_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN10',
                    'metric': 'No inconsistent values',
                    'metric_description': 'Verifies the correct usage of irreflexive properties.',
                    'score': ratio,
                    'message': f'{count_irreflexive_properties_shapes - irreflexive_property_ones} properties don\'t conform to their irreflexive characteristic' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of irreflexive properties correctly used / Number of irreflexive properties",
                    'shape_template': '',
                    'violations': '; '.join([f'({p},{s})' for p, s in irreflexive_properties_properties]),
                    'num_violations': len(irreflexive_properties_properties),
                    "vocab": ''
                })

            # Misuse object properties
            if count_object_misuse_properties_shapes > 0:
                ratio = (misuse_object_properties_ones/count_object_misuse_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN3',
                    'metric': 'No misuse of owl:DatatypeProperty or owl:ObjectProperty',
                    'metric_description': 'Verifies that owl:ObjectProperty aren\'t used with Literals',
                    'score': ratio,
                    'message': f'{count_object_misuse_properties_shapes - misuse_object_properties_ones} object properties aren\'t used with the correct range' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of owl:ObjectProperty correctly used / Number of owl:ObjectProperty",
                    'shape_template': 'ex:MisuseOwlObjectPropertiesShape\na sh:NodeShape ;\nsh:targetObjectsOf ex:SomeObjectProperty ;\nsh:nodeKind sh:IRI.',
                    'violations': '; '.join([f'({p},{s})' for p, s in misuse_object_properties_properties]),
                    'num_violations': len(misuse_object_properties_properties),
                    "vocab": ''
                })

            # Misuse datatype properties
            if count_datatype_misuse_properties_shapes > 0:
                ratio = (misuse_datatype_properties_ones/count_datatype_misuse_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN3',
                    'metric': 'No misuse of owl:DatatypeProperty or owl:ObjectProperty',
                    'metric_description': 'Verifies that owl:DatatypeProperty are used with Literals',
                    'score': ratio,
                    'message': f'{count_datatype_misuse_properties_shapes - misuse_datatype_properties_ones} datatype properties aren\'t used with the correct range' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of owl:DatatypeProperty correctly used / Number of owl:DatatypeProperty",
                    'shape_template': 'ex:MisuseOwlDatatypePropertiesShape\na sh:NodeShape ;\nsh:targetObjectsOf ex:SomeDatatypeProperty ;\nsh:nodeKind sh:Literal.',
                    'violations': '; '.join([f'({p},{s})' for p, s in misuse_datatype_properties_properties]),
                    'num_violations': len(misuse_datatype_properties_properties),
                    "vocab": ''
                })

            # Inverse functional properties
            if count_inverse_functional_properties_shapes > 0:
                ratio = (inverse_functional_property_ones/count_inverse_functional_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN5',
                    'metric': 'Valid usage of inverse-functional properties',
                    'metric_description': 'Verifies the correct usage of inverse-functional properties.',
                    'score': ratio,
                    'message': f'{count_inverse_functional_properties_shapes - inverse_functional_property_ones} properties don\'t conform to their inverse functional characteristic' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of inverse-functional properties correctly used / Number of inverse-functional properties",
                    'shape_template': 'ex:InverseFunctionalPropertyUniquenessShape\na sh:NodeShape ;\nsh:targetObjectsOf ex:someInvFuncProp ;\nsh:property [\nsh:path [ sh:inversePath ex:someInvFuncProp ];\nsh:maxCount 1;\n].',
                    'violations': '; '.join([f'({p},{s})' for p, s in inverse_functional_properties_properties]),
                    'num_violations': len(inverse_functional_properties_properties),
                    "vocab": ''
                })

            if count_functional_properties_shapes > 0:
                ratio = (functional_property_ones/count_functional_properties_shapes)
                rows.append({
                    'dimension': 'Consistency',
                    'metric_id': 'CN10',
                    'metric': 'No inconsistent values',
                    'metric_description': 'Verifies the correct usage of functional properties.',
                    'score': ratio,
                    'message': f'{count_functional_properties_shapes - functional_property_ones} properties don\'t conform to their functional characteristic' if ratio < 1 else '',
                    'metric_type': 'count',
                    'metric_calculation': '1 - (Number of violations / Number of triples that use the property)',
                    "meta_metric_calculation": "Number of functional properties correctly used / Number of functional properties",
                    "shape_template": "ex:FunctionalPropertyShape\\na sh:NodeShape ;\\nsh:targetSubjectsOf {{property_uri}} ;\\nsh:property [\\n    sh:path {{property_uri}} ;\\n    sh:maxCount 1 ;\\n] .",
                    'violations': '; '.join([f'({p},{s})' for p, s in functional_properties_properties]),
                    'num_violations': len(functional_properties_properties),
                    "vocab": ''
                })

            # Schema completeness class usage
            if count_schema_completeness_class_usage_shapes > 0:
                ratio = (schema_completeness_class_usage_ones/count_schema_completeness_class_usage_shapes)
                rows.append({
                    'dimension': 'Completeness',
                    'metric_id': 'CP1',
                    'metric': 'Schema completeness',
                    'metric_description': 'Verifies that classes defined in vocabularies are used in the dataset.',
                    'score': ratio,
                    'message': f'{count_schema_completeness_class_usage_shapes - schema_completeness_class_usage_ones} classes aren\'t used in the dataset' if ratio < 1 else '',
                    'metric_type': 'binary',
                    "metric_calculation": "1 if the class is used, 0 otherwise",
                    "meta_metric_calculation": "Number of classes used / Number of classes defined in vocabularies",
                    'shape_template': 'ex:SchemaCompletenessClassUsageShape\na sh:NodeShape ;\nsh:targetNode CLASS_URI ;\nsh:property [\nsh:path [ sh:inversePath rdf:type ];\nsh:minCount 1;\n].',
                    'violations': '; '.join(schema_completeness_class_usage_classes),
                    'num_violations': len(schema_completeness_class_usage_classes),
                    "vocab": ''
                })
            
            if count_incompatible_dataype_shapes > 0:
                ratio = (incompatible_dataype_ones / count_incompatible_dataype_shapes)
                rows.append({
                    "dimension": "Syntactic Validity",
                    "metric_id": "SV3",
                    "metric": "No malformed datatype literals",
                    "score": ratio,
                    "message": "",
                    "metric_description": "Verifies that datatype properties aren't used with incorrect datatypes.",
                    "metric_type": "count",
                    "metric_calculation": "1 - (Number of violations / Number of triples that use the property)",
                    "meta_metric_calculation": "Number of correctly used properties / Number of properties with a datatype range",
                    "shape_template": "ex:MemberIncompatibleDatatypeShape\na sh:NodeShape ;\nsh:targetSubjectsOf PROPERTY_URI ;\nsh:property [\n    sh:path PROPERTY_URI ;\n    sh:datatype DATATYPE_URI \n] .",
                    "violations": "; ".join([f'({p},{s})' for p, s in incompatible_dataype_properties]),
                    "num_violations": len(incompatible_dataype_properties),
                    "vocab": ''
                })

            if count_malformed_dataype_shapes > 0:
                ratio = (malformed_dataype_ones / count_malformed_dataype_shapes)
                rows.append({
                    "dimension": "Syntactic Validity",
                    "metric_id": "SV3",
                    "metric": "No malformed datatype literals",
                    "score": ratio,
                    "message": "",
                    "metric_description": "Verifies that datatype property's values follow the expected lexical syntax of the datatype.",
                    "metric_type": "count",
                    "metric_calculation": "1 - (Number of violations / Number of triples that use the property)",
                    "meta_metric_calculation": "Number of correctly used properties / Number of properties with a datatype range",
                    "shape_template": "ex:MalformedDatatypeShape \\na sh:NodeShape ;\\nsh:targetSubjectsOf PROPERTY_URI ;\\nsh:property [\\n    sh:path PROPERTY_URI ;\\n    sh:pattern DATATYPE_PATTERN;\\n] .",
                    "violations": "; ".join([f'({p},{s})' for p, s in malformed_dataype_properties]),
                    "num_violations": len(malformed_dataype_properties),
                    "vocab": ''
                })
            
            if len(count_undefined_properties_shapes.keys()) > 0:

                for vocab in count_undefined_properties_shapes.keys():
                    ratio = (undefined_properties_ones[vocab] / count_undefined_properties_shapes[vocab])
                    rows.append({
                        "dimension": "Interpretability",
                        "metric_id": "ITP3",
                        "metric": "Invalid usage of undefined classes and properties",
                        "score": ratio,
                        "message": "",
                        "metric_description": "Verifies that the properties used in the dataset are defined in the vocabulary.",
                        "metric_type": "binary",
                        "metric_calculation": "1 if the property is defined, 0 otherwise",
                        "meta_metric_calculation": "Number of defined properties / Number of properties used in the dataset",
                        "shape_template": "ex:UndefinedPropertyShape \\na sh:NodeShape ;\\nsh:targetNode PROPERTY_URI ;\\nsh:property [\\n    sh:path TYPE_PROPERTY ;\\n    sh:class rdf:Property ;\\n    sh:minCount 1 ;\\n    sh:maxCount 1 \\n] .",
                        "violations": "; ".join(undefined_properties_properties[vocab]),
                        "num_violations": len(undefined_properties_properties[vocab]),
                        "vocab": vocab
                    })

            if len(count_undefined_classes_shapes.keys()) > 0:
                for vocab in count_undefined_classes_shapes.keys():
                    ratio = (undefined_classes_ones[vocab] / count_undefined_classes_shapes[vocab])
                    rows.append({
                        "dimension": "Interpretability",
                        "metric_id": "ITP3",
                        "metric": "Invalid usage of undefined classes and properties",
                        "score": ratio,
                        "message": "",
                        "metric_description": "Verifies that the classes used in the dataset are defined in the vocabulary.",
                        "metric_type": "binary",
                        "metric_calculation": "1 if the class is defined, 0 otherwise",
                        "meta_metric_calculation": "Number of defined classes / Number of classes used in the dataset",
                        "shape_template": "ex:UndefinedClassShape \\na sh:NodeShape ;\\nsh:targetNode CLASS_URI ;\\nsh:property [\\n    sh:path TYPE_PROPERTY ;\\n    sh:class rdfs:Class ;\\n    sh:minCount 1 ;\\n    sh:maxCount 1 ;\\n] .",
                        "violations": "; ".join(undefined_classes_classes[vocab]),
                        "num_violations": len(undefined_classes_classes[vocab]),
                        "vocab": vocab
                    })

            # this shape is instantiated for every property used in the dataset that
            # has a domain defined
            if count_correct_domain_shapes > 0:
                self.graph_profile['num_properties_domain'] = count_correct_domain_shapes

            # this shape is instantiated for every property defined in the vocab
            if count_misuse_properties_shapes > 0:
                self.graph_profile['num_properties_vocabularies'] = count_misuse_properties_shapes

            # this shapes is instantiated for every class defined in the vocab
            if count_schema_completeness_class_usage_shapes > 0:
                self.graph_profile['num_classes_vocabularies'] = count_schema_completeness_class_usage_shapes

        output_csv_path = f'{results_folder}/dq_assessment_{self.dataset_name}.csv'

        with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['dimension','metric_id', 'metric', 
                                                         'score', 'message', 'metric_description', 'metric_type', 
                                                         'metric_calculation', 'meta_metric_calculation', 'shape_template',
                                                         'violations', 'num_violations', 'vocab'])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        self.counter_shapes = counter_shapes
