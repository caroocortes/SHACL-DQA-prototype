import json
import copy
from const import *
from utils import *

class SHACLShapeBuilder:
    """
        Instantiates SHACL shapes
    """
    def __init__(self, dq_assessment):
        self.type_property = dq_assessment.type_property
        self.labeling_property = dq_assessment.labeling_property
        self.description_property = dq_assessment.description_property
        self.interlinking_property = dq_assessment.interlinking_property
        self.type_property = dq_assessment.type_property
        self.uris_max_length = dq_assessment.uris_max_length
        self.base_namespace = dq_assessment.base_namespace

        self.regex_pattern = None
        self.uri_space = None

        self.config = dq_assessment.config
        self.vocab_names = dq_assessment.vocab_names
        self.dataset_name = dq_assessment.dataset_name
        self.template = dq_assessment.data_template

        self.counter ={
            "count_owl_datatype_properties": 0,
            "count_owl_object_properties": 0,
            "count_datatype_range_props": 0,
            "count_range_props": 0,
            "count_domain_props": 0,
            "count_irreflexive_props": 0,
            "count_functional_props": 0,
            "count_inverse_functional_props": 0,
            "count_deprecated_classes": 0,
            "count_deprecated_properties": 0,
            "property_counter": 1,
            "property_counter_map": {},
            "class_counter": 1,
            "class_counter_map": {}
        }
        # Stores the results for metrics that need to be instantiated 
        # with specific information of classes and properties
        self.dq_results_intrinsic = {}

    def accessibility_data_shapes(self):

        shacl_shapes = ''

        shacl_shapes += self.template.module.interlinking_external_uris(self.base_namespace, self.interlinking_property) + '\n'
        shacl_shapes += self.template.module.performance_hash_uris_entities(self.type_property)
         
        return shacl_shapes
    

    def contextual_data_shapes(self):
        shacl_shapes = self.template.module.understandability_label_entities(self.type_property, self.labeling_property) + '\n'
        
        # Check if the metric URIRegexPressence is 1, hence, 
        # there's a regex pattern provided for the URIs
        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        results_file = f'{folder_path}/dq_assessment_{self.dataset_name}_metadata.json'
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        metadata_file_path = self.config['settings']['metadata_file']
        metadata_file_format = self.config['settings']['metadata_file_format']
        if "URISpacePressence" in results and results["URIRegexPressence"]['measure'] == 1:
            # If the metric is 1, we need to check the regex pattern against the URIs
            self.regex_pattern = get_uri_regex_pattern(metadata_file_path, metadata_file_format)
            shacl_shapes += self.template.module.understandability_uri_regex_compliance_entities(self.type_property, escape_dots_for_turtle_regex(self.regex_pattern))
        
        if "URISpacePressence" in results and results["URISpacePressence"]['measure'] == 1:
            self.uri_space = get_uri_space(metadata_file_path, metadata_file_format)
            shacl_shapes += self.template.module.understandability_uri_space_compliance_entities(self.type_property, self.uri_space)
            
        return self.regex_pattern, self.uri_space, shacl_shapes

    
    def representational_data_shapes(self, graph_profile):
        max_length_value = self.uris_max_length
        shacl_shapes = ''

        shacl_shapes += self.template.module.representational_conciseness_uris_length(self.type_property, max_length_value) + '\n'
        shacl_shapes += self.template.module.representational_conciseness_uris_parameters(self.type_property) + '\n'
        shacl_shapes += self.template.module.representational_conciseness_prolix_features(self.type_property) + '\n'
        
        if self.labeling_property:
            shacl_shapes += self.template.module.versatility_languages_labels_entities(self.type_property, self.labeling_property) + '\n'
            
        if self.description_property:
            shacl_shapes += self.template.module.versatility_languages_descriptions_entities(self.type_property, self.description_property) + '\n'
            
        shacl_shapes += self.template.module.interpretability_self_descriptive_formats(self.type_property) + '\n'
        shacl_shapes += self.template.module.interpretability_usage_blank_nodes(self.type_property) + '\n'

        property_counter = 0
        property_counter_map = {}
        dq_results = {}
        for prop in graph_profile['properties']:
            shacl_shapes += self.template.module.interpretability_self_descriptive_format_properties(property_counter, prop) + '\n'
            
            metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['SelfDescriptiveFormatProperties'])
            metric_info['shape'] = f'ex:SelfDescriptiveFormatPropertiesShape_{property_counter}'
            metric_name = f'SelfDescriptiveFormatProperties_{property_counter}'
            dq_results[metric_name] = metric_info
            
            property_counter_map[property_counter] = prop
            property_counter += 1

        # Store specific result
        file_path = DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
            # Update existing data with new initial results
            existing_data.update(dq_results)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4)
        else:
            # If file doesn't exist, create it with dq_results
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dq_results, f, indent=4)

        return shacl_shapes, property_counter_map
    
    def create_metric_info_class(self, metric_name, class_uri=None, classes=None):
        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC[metric_name])
        metric_info['shape'] = f'ex:{metric_name}Shape_{self.counter["class_counter"]}'
        metric_name = f'{metric_name}_{self.counter["class_counter"]}'
        self.dq_results_intrinsic[metric_name] = metric_info

        if metric_name.startswith('EntitiesDisjointClasses'):
            self.counter["class_counter_map"][self.counter["class_counter"]] = {
                'first_class': str(classes[0]),
                'second_class': str(classes[1])
            }
        else:
            self.counter["class_counter_map"][self.counter["class_counter"]] = str(class_uri)
        self.counter["class_counter"] += 1


    def create_metric_info_prop(self, metric_name, prop):
        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC[metric_name])
        metric_info['shape'] = f'ex:{metric_name}Shape_{self.counter["property_counter"]}'
        metric_name = f'{metric_name}_{self.counter["property_counter"]}'
        self.dq_results_intrinsic[metric_name] = metric_info

        self.counter["property_counter_map"][self.counter["property_counter"]] = prop
        self.counter["property_counter"] += 1


    def correct_domain_shape(self, prop, domain):
        shape = self.template.module.consistency_correct_domain(self.counter["property_counter"], prop, domain) + '\n'

        metric_name = "CorrectDomain"
        self.create_metric_info_prop(metric_name, prop)

        return shape
    
    def correct_domain_node_kind_shape(self, prop):
        shape = self.template.module.consistency_correct_domain_node_kind(self.counter["property_counter"], prop) + '\n'

        metric_name = "CorrectDomain"
        self.create_metric_info_prop(metric_name, prop)

        return shape
    
    def correct_range_object_shape(self, prop, range_value):

        shape = self.template.module.consistency_correct_range_object(self.counter["property_counter"], prop, range_value) + '\n'
        metric_name = "CorrectRange"
        self.create_metric_info_prop(metric_name, prop)
        
        return shape
    
    def correct_range_datatype_shape(self, prop, range_value=None):

        shape = self.template.module.consistency_correct_range_datatype(self.counter["property_counter"], prop, range_value) + '\n'
        metric_name = "CorrectRange"
        self.create_metric_info_prop(metric_name, prop)
        
        return shape
    
    def correct_range_node_kind_shape(self, prop, node_kind):
        
        if node_kind == 'Literal':
            shape = self.template.module.consistency_correct_range_node_kind_literal(self.counter["property_counter"], prop) + '\n'
        elif node_kind == 'BlankNodeOrIri':
            shape = self.template.module.consistency_correct_range_node_kind_owl_thing(self.counter["property_counter"], prop) + '\n'
        else:
            shape = self.template.module.consistency_correct_range_node_kind_rdfs_resource(self.counter["property_counter"], prop) + '\n'
        
        metric_name = "CorrectRange"
        self.create_metric_info_prop(metric_name, prop)
        return shape

    def misuse_owl_datatype_properties(self, prop):

        shape = self.template.module.consistency_misuse_datatype_properties(self.counter["property_counter"], prop) + '\n'
                        
        metric_name = "MisuseOwlDatatypeProperties"
        self.create_metric_info_prop(metric_name, prop)

        return shape
    
    def misuse_owl_object_properties(self, prop):
        shape = self.template.module.consistency_misuse_object_properties(self.counter["property_counter"], prop) + '\n'
        metric_name = "MisuseOwlObjectProperties"
        self.create_metric_info_prop(metric_name, prop)

        return shape

    def misplaced_properties(self, prop):
        shape = self.template.module.consistency_misplaced_properties(self.counter["property_counter"], prop, self.type_property) + '\n'
        metric_name = "MisplacedProperties"
        self.create_metric_info_prop(metric_name, prop)
        return shape


    def member_incompatible_datatype(self, prop, range_value):
        shape = self.template.module.syntactic_validity_incompatible_datatype(self.counter["property_counter"], prop, range_value) + '\n'
                            
        metric_name = "MemberIncompatibleDatatype"
        self.create_metric_info_prop(metric_name, prop)

        return shape
    
    def malformed_datatype(self, prop, regex_pattern):
        shape = self.template.module.syntactic_validity_malformed_datatype(self.counter["property_counter"], prop, python_regex_to_shacl_regex(regex_pattern)) + '\n'
        metric_name = "MalformedDatatype"
        self.create_metric_info_prop(metric_name, prop)

        return shape
    
    def irreflexive_properties(self, prop):
        shape = self.template.module.consistency_irreflexive_property(self.counter["property_counter"], prop) + '\n'
        metric_name = "IrreflexiveProperty"
        self.create_metric_info_prop(metric_name, prop)
        return shape
    
    def deprecated_properties(self, prop):
        shape = self.template.module.consistency_deprecated_properties(self.counter["property_counter"], prop, self.type_property) + '\n'
        metric_name = "DeprecatedProperties"
        self.create_metric_info_prop(metric_name, prop)
        return shape

    def inverse_functional_properties(self, prop):
        shape = self.template.module.consistency_inverse_functional_property(self.counter["property_counter"], prop) + '\n'
        metric_name = "InverseFunctionalPropertyUniqueness"
        self.create_metric_info_prop(metric_name, prop)
        return shape

    def functional_properties(self, prop):
        shape = self.template.module.consistency_functional_property(self.counter["property_counter"], prop) + '\n'
        metric_name = "FunctionalProperty"
        self.create_metric_info_prop(metric_name, prop)
        return shape
    
    def intrinsic_data_shapes(self, graph_profile):

        shacl_shapes = ''

        shacl_shapes += self.template.module.interlinking_completeness(self.type_property, self.interlinking_property)

        properties_in_dataset = graph_profile['properties']
        classes_in_dataset = graph_profile['classes']

        properties_misplaced = []

        for vocab in self.vocab_names:
            vocab_name = self.config[vocab]['vocab_name']
            with open(f'{PROFILE_VOCABULARIES_FOLDER_PATH}/{vocab_name}.json', 'r', encoding='utf-8') as f:
                vocab_profile = json.load(f)

            if len(vocab_profile['classes']) > 0:
                for class_uri in vocab_profile['classes']:

                    shacl_shapes += self.template.module.completeness_schema_completeness_class_usage(self.counter["class_counter"], class_uri, self.type_property)
                    metric_name = "SchemaCompletenessClassUsage"
                    self.create_metric_info_class(metric_name, class_uri=str(class_uri), classes=None)

                    shacl_shapes += self.template.module.consistency_misplaced_classes(self.counter["class_counter"], class_uri, self.type_property)
                    metric_name = "MisplacedClasses"
                    self.create_metric_info_class(metric_name, class_uri=str(class_uri), classes=None)

            if len(vocab_profile['disjoint_classes']) > 0:
                for classes in vocab_profile['disjoint_classes']:
                    if classes[0] in classes_in_dataset:
                        shacl_shapes += self.template.module.consistency_entities_disjoint_classes(self.counter["class_counter"], classes[0], classes[1]) + '\n'
                        metric_name = "EntitiesDisjointClasses"
                        self.create_metric_info_class(metric_name, class_uri=None, classes=classes)

            if len(vocab_profile['object_properties']) > 0:
                for prop, info in vocab_profile['object_properties'].items():
                    
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    if prop in properties_in_dataset:
                        self.counter['count_owl_object_properties'] += 1
                        shacl_shapes += self.misuse_owl_object_properties(prop)

                        if info['domain']:
                            self.counter['count_domain_props'] += 1
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += self.correct_domain_shape(prop, info['domain'])
                            else:
                                shacl_shapes += self.correct_domain_node_kind_shape(prop)

                        if info['range']:
                            self.counter['count_range_props'] += 1
                            if info['range'] == 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += self.correct_range_node_kind_shape(prop, node_kind='BlankNodeOrIri')
                            elif info['range'] == 'http://www.w3.org/2000/01/rdf-schema#Resource':
                                shacl_shapes += self.correct_range_node_kind_shape(prop, node_kind='both')
                            else:
                                shacl_shapes += self.correct_range_object_shape(prop, info['range']) 

            if len(vocab_profile['datatype_properties']) > 0:
                for prop, info in vocab_profile['datatype_properties'].items():
                    
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    if prop in properties_in_dataset:
                        self.counter['count_owl_datatype_properties'] += 1
                        shacl_shapes += self.misuse_owl_datatype_properties(prop)

                        if info['domain']:
                            self.counter['count_domain_props'] += 1
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += self.correct_domain_shape(prop, info['domain'])
                            else:
                                shacl_shapes += self.correct_domain_node_kind_shape(prop)

                        if info['range']:
                            
                            self.counter['count_range_props'] += 1
                            self.counter["count_datatype_range_props"] += 1

                            shacl_shapes += self.correct_range_datatype_shape(prop, info['range'])
                            shacl_shapes += self.member_incompatible_datatype(prop, info['range'])

                            datatype = info['range']
                            regex_pattern = REGEX_PATTERNS_DICT[datatype] if datatype in REGEX_PATTERNS_DICT else None
                            
                            if regex_pattern:
                                shacl_shapes += self.malformed_datatype(prop, regex_pattern)

            if len(vocab_profile['irreflexive']) > 0:
                for prop in vocab_profile['irreflexive']:
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    if prop in properties_in_dataset:
                        self.counter['count_irreflexive_props'] += 1
                        shacl_shapes += self.irreflexive_properties(prop)

            if len(vocab_profile['inverse_functional']) > 0:
                for prop in vocab_profile['inverse_functional']:
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    if prop in properties_in_dataset:
                        self.counter['count_inverse_functional_props'] += 1
                        shacl_shapes +=  self.inverse_functional_properties(prop)

            if len(vocab_profile['functional']) > 0:
                for prop in vocab_profile['functional']:

                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)
                    
                    if prop in properties_in_dataset:
                        self.counter['count_functional_props'] += 1
                        shacl_shapes += self.functional_properties(prop)

            if len(vocab_profile['deprecated_classes']) > 0:
                classes_list = " ".join([f"<{v}>" for v in vocab_profile['deprecated_classes']])
                shacl_shapes += self.template.module.consistency_deprecated_classes(classes_list, self.type_property) + '\n'
                
                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['DeprecatedClasses'])
                metric_info['shape'] = f'ex:DeprecatedClassesShape'
                metric_name = f'DeprecatedClasses'
                self.dq_results_intrinsic[metric_name] = metric_info

                self.counter['count_deprecated_classes'] = len(classes_list)

            if len(vocab_profile['deprecated_properties']) > 0:
                for prop in vocab_profile['deprecated_properties']:
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    self.counter['count_deprecated_properties'] += 1
                    shacl_shapes += self.deprecated_properties(prop)

            if len(vocab_profile['rdf_properties']) > 0:
                # In this case we don't filter properties that aren't used in the dataset
                # since we want to check the correct usage of properties (that they are not used as a class)
                for prop, info in vocab_profile['rdf_properties'].items():

                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

                    if prop in properties_in_dataset:
                        if info['domain']:
                            self.counter['count_domain_props'] += 1
                            # rdfs:Resource can't be a domain because it includes Literals
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += self.correct_domain_shape(prop, info['domain'])
                            else:
                                shacl_shapes += self.correct_domain_node_kind_shape(prop)

                        if info['range']:
                            self.counter["count_range_props"] += 1
                            if info['range']['type'] == 'literal':
                                
                                if info['range']['value'] != 'http://www.w3.org/2000/01/rdf-schema#Literal':
                                    self.counter["count_datatype_range_props"] += 1
                                    shacl_shapes += self.correct_range_datatype_shape(prop, info['range']['value'])
                                    shacl_shapes += self.member_incompatible_datatype(prop, info['range']['value'])

                                    datatype = info['range']['value']
                                    regex_pattern = REGEX_PATTERNS_DICT[datatype] if datatype in REGEX_PATTERNS_DICT else None
                                    
                                    if regex_pattern:
                                        shacl_shapes += self.malformed_datatype(prop, regex_pattern)
                                else:
                                    shacl_shapes += self.correct_range_node_kind_shape(prop, node_kind='Literal')
                            else:
                                if info['range'] == 'http://www.w3.org/2002/07/owl#Thing':
                                    shacl_shapes += self.correct_range_node_kind_shape(prop, node_kind='BlankNodeOrIri')
                                elif info['range'] == 'http://www.w3.org/2000/01/rdf-schema#Resource':
                                    shacl_shapes += self.correct_range_node_kind_shape(prop, node_kind='both')
                                else: # specific class
                                    shacl_shapes += self.correct_range_object_shape(prop, info['range']['value'])
            
            if len(vocab_profile['transitive']) > 0:
                for prop in vocab_profile['transitive']:
                    # have to check this because if a transitive/reflexive/asymmetric property has 
                    # a range/domain they will be in the rdf_properties dict
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

            if len(vocab_profile['reflexive']) > 0:
                for prop in vocab_profile['reflexive']:
                    
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

            if len(vocab_profile['asymmetric']) > 0:
                for prop in vocab_profile['asymmetric']:
                    
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

            if len(vocab_profile['symmetric']) > 0:
                for prop in vocab_profile['symmetric']:
                    
                    if prop not in properties_misplaced:
                        shacl_shapes += self.misplaced_properties(prop)
                        properties_misplaced.append(prop)

        # Add number of owl:DatatypeProperty and owl:ObjectProperty
        graph_profile['count_owl_datatype_properties'] = self.counter['count_owl_datatype_properties']
        graph_profile['count_owl_object_properties'] = self.counter['count_owl_object_properties']

        graph_profile['count_domain_props'] = self.counter['count_domain_props']

        # Add number of properties with datatype range and object range
        graph_profile['count_range_props'] = self.counter['count_range_props']
        graph_profile['count_datatype_range_props'] = self.counter['count_datatype_range_props']

        # Add number of irreflexive properties
        graph_profile['count_irreflexive_props'] = self.counter['count_irreflexive_props']

        # Add number of inverse-functional properties
        graph_profile['count_inverse_functional_props'] = self.counter['count_inverse_functional_props']

        # Add number of functional properties
        graph_profile['count_functional_props'] = self.counter['count_functional_props']

        # Add number of dperecated classes
        graph_profile['count_deprecated_classes'] = self.counter['count_deprecated_classes']

        # Add number of deprecated properties
        graph_profile['count_deprecated_properties'] = self.counter['count_deprecated_properties']
        
        # Update profile with new information from vocabularies
        with open(f'{PROFILE_DATASETS_FOLDER_PATH}/{self.dataset_name}.json', 'w', encoding='utf-8') as f:
            json.dump(graph_profile, f, indent=4)

        # Save the DQ "initial" results for the shapes that need instantiation from vocabularies
        file_path = DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
            # Update existing data with new initial results
            existing_data.update(self.dq_results_intrinsic)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4)
        else:
            # If file doesn't exist, create it with dq_results
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.dq_results_intrinsic, f, indent=4)

        return shacl_shapes, graph_profile, self.counter['property_counter_map'], self.counter['class_counter_map']

    def vocabulary_shapes(self, dq_assessment, vocab, property_vocab_map, class_vocab_map):
        shacl_shapes = ''
        template = dq_assessment.vocabs_template

        shacl_shapes += template.module.understandability_label_classes(self.labeling_property) + '\n'
        shacl_shapes += template.module.understandability_label_properties(self.labeling_property)

        vocab_name = dq_assessment.config[vocab]["vocab_name"]
        
        dq_results = {}

        counter_class = 0
        counter_property = 0

        if vocab_name in class_vocab_map:
            classes_vocab = class_vocab_map[vocab_name]
            for class_ in classes_vocab:
                shacl_shapes += template.module.versatility_undefined_class(counter_class, class_, self.type_property)
                metric_info = copy.deepcopy(DQ_MEASURES_VOCABULARY_SPECIFIC['UndefinedClass'])
                metric_info['shape'] = f'ex:UndefinedClassShape_{counter_class}'
                metric_name = f'UndefinedClass_{counter_class}'
                dq_results[metric_name] = metric_info

                counter_class += 1
    
        if vocab_name in property_vocab_map:
            properties_vocab = property_vocab_map[vocab_name]
            for prop_ in properties_vocab:
                shacl_shapes += template.module.versatility_undefined_property(counter_property, prop_, self.type_property)
                
                metric_info = copy.deepcopy(DQ_MEASURES_VOCABULARY_SPECIFIC['UndefinedProperty'])
                metric_info['shape'] = f'ex:UndefinedPropertyShape_{counter_property}'
                metric_name = f'UndefinedProperty_{counter_property}'
                dq_results[metric_name] = metric_info

                counter_property += 1
        
        # Store specific results
        file_path = DQ_MEASURES_VOCABULARIES_SPECIFIC_TEMPLATE_FILE_PATH
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dq_results, f, indent=4)

        return shacl_shapes