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

        self.config = dq_assessment.config
        self.vocab_names = dq_assessment.vocab_names
        self.dataset_name = dq_assessment.dataset_name

    def accessibility_data_shapes(self, template):

        shacl_shapes = ''

        shacl_shapes += template.module.interlinking_external_uris(self.base_namespace, self.interlinking_property) + '\n'
        shacl_shapes += template.module.performance_hash_uris_entities(self.type_property)
         
        return shacl_shapes
    

    def contextual_data_shapes(self, template):
        shacl_shapes = template.module.understandability_label_entities(self.type_property, self.labeling_property) + '\n'
        
        # Check if the metric URIRegexPresence is 1, hence, 
        # there's a regex pattern provided for the URIs
        folder_path = DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=self.dataset_name)
        results_file = f'{folder_path}/dq_assessment_{self.dataset_name}_metadata.json'
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        metric_name = "URIRegexPresence"

        if metric_name in results and results[metric_name] == 1:
            # If the metric is 1, we need to check the regex pattern against the URIs
            self.regex_pattern = get_uri_regex_pattern(self.config.metadata_file, self.config.metadata_file_format)
            shacl_shapes += template.module.understandability_uri_regex_compliance_entities(self.type_property, self.regex_pattern)
            
        return self.regex_pattern, shacl_shapes

    
    def representational_data_shapes(self, template):
        max_length_value = self.uris_max_length
        shacl_shapes = ''

        shacl_shapes += template.module.representational_conciseness_uris_length(self.type_property, max_length_value) + '\n'
        shacl_shapes += template.module.representational_conciseness_uris_parameters(self.type_property) + '\n'
        shacl_shapes += template.module.representational_conciseness_prolix_features(self.type_property) + '\n'
        
        if self.labeling_property:
            shacl_shapes += template.module.versatility_languages_labels_entities(self.type_property, self.labeling_property) + '\n'
            
        if self.description_property:
            shacl_shapes += template.module.versatility_languages_descriptions_entities(self.type_property, self.description_property) + '\n'
            
        shacl_shapes += template.module.versatility_self_descriptive_formats(self.type_property) + '\n'
        shacl_shapes += template.module.versatility_usage_blank_nodes(self.type_property) + '\n'
        
        return shacl_shapes
    

    def intrinsic_data_shapes(self, template, graph_profile):

        shacl_shapes = ''

        shacl_shapes += template.module.interlinking_completeness(self.type_property, self.interlinking_property)
        
        # Stores the results for metrics that need to be instantiated 
        # with specific information of classes and properties
        dq_results = {}

        properties_in_dataset = graph_profile['properties']
        classes_in_dataset = graph_profile['classes']

        count_dt_props_dataset = 0
        count_o_props_dataset = 0

        count_datatype_range_props = 0
        count_object_range_props = 0
        count_irreflexive_props = 0
        count_functional_props = 0
        count_inverse_functional_props = 0
        count_deprecated_classes = 0
        count_deprecated_properties = 0

        property_counter = 1
        property_counter_map = {}

        class_counter = 1
        class_counter_map = {}

        for vocab in self.vocab_names:
            vocab_name = self.config[vocab]['vocab_name']
            with open(f'{PROFILE_VOCABULARIES_FOLDER_PATH}/{vocab_name}.json', 'r', encoding='utf-8') as f:
                vocab_profile = json.load(f)

            if len(vocab_profile['classes']) > 0:
                for class_uri in vocab_profile['classes']:

                    if class_uri not in [RDF.Property, RDFS.Class]:
     
                        shacl_shapes += template.module.completeness_schema_completeness_class_usage(class_counter, class_uri, self.type_property)

                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['SchemaCompletenessClassUsage'])
                        metric_info['shape'] = f'ex:SchemaCompletenessClassUsageShape_{class_counter}'
                        metric_name = f'SchemaCompletenessClassUsage_{class_counter}'
                        dq_results[metric_name] = metric_info

                        class_counter_map[class_counter] = str(class_uri)
                        class_counter += 1

            if len(vocab_profile['disjoint_classes']) > 0:
                for classes in vocab_profile['disjoint_classes']:
                    if classes[0] in classes_in_dataset:
                        
                        shacl_shapes +=  template.module.consistency_entities_disjoint_classes(class_counter, classes[0], classes[1]) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['EntitiesDisjointClasses'])
                        metric_info['shape'] = f'ex:EntitiesDisjointClassesShape_{class_counter}'
                        metric_name = f'EntitiesDisjointClasses_{class_counter}'
                        dq_results[metric_name] = metric_info

                        class_counter_map[class_counter] = {
                            'first_class': str(classes[0]),
                            'second_class': str(classes[1])
                        }
                        class_counter += 1

            if len(vocab_profile['object_properties']) > 0:
                for prop, info in vocab_profile['object_properties'].items():
                    
                    if prop in properties_in_dataset:
                        
                        count_o_props_dataset += 1
                        shacl_shapes += template.module.consistency_misuse_object_properties(property_counter, prop) + '\n'

                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MisuseOwlObjectProperties'])
                        metric_info['shape'] = f'ex:MisuseOwlObjectPropertiesShape_{property_counter}'
                        metric_name = f'MisuseOwlObjectProperties_{property_counter}'
                        dq_results[metric_name] = metric_info
                        
                        property_counter_map[property_counter] = prop
                        property_counter += 1

                        if info['domain']:

                            # only consider specific classes
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += template.module.consistency_correct_domain(property_counter, prop, info['domain']) + '\n'
                                

                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectDomain'])
                                metric_info['shape'] = f'ex:CorrectDomainShape_{property_counter}'
                                metric_name = f'CorrectDomain_{property_counter}'
                                dq_results[metric_name] = metric_info
                                
                                property_counter_map[property_counter] = prop
                                property_counter += 1

                        if info['range']:
                            
                            # only consider specific classes
                            if info['range'] != 'http://www.w3.org/2002/07/owl#Thing':

                                count_object_range_props += 1
                                shacl_shapes += template.module.consistency_correct_range_object(property_counter, prop, info['range']) + '\n'
                                

                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectRangeObject'])
                                metric_info['shape'] = f'ex:CorrectRangeObjectShape_{property_counter}'
                                metric_name = f'CorrectRangeObject_{property_counter}'
                                dq_results[metric_name] = metric_info
                                
                                property_counter_map[property_counter] = prop
                                property_counter += 1
                    else:
                        # In this case we don't filter properties that aren't used in the dataset
                        # since we want to check the correct usage of properties (that they are not used as a class)
                        shacl_shapes +=  template.module.consistency_misuse_properties(property_counter, prop, self.type_property) + '\n'
                    
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MisplacedProperties'])
                        metric_info['shape'] = f'ex:MisplacedPropertiesShape_{property_counter}'
                        metric_name = f'MisplacedProperties_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

            if len(vocab_profile['datatype_properties']) > 0:
                for prop, info in vocab_profile['datatype_properties'].items():
                    
                    if prop in properties_in_dataset:
                        count_dt_props_dataset += 1

                        shacl_shapes += template.module.consistency_misuse_datatype_properties(property_counter, prop) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MisuseOwlDatatypeProperties'])
                        metric_info['shape'] = f'ex:MisuseOwlDatatypePropertiesShape_{property_counter}'
                        metric_name = f'MisuseOwlDatatypeProperties_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

                        if info['domain']:

                            # only consider specific classes
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += template.module.consistency_correct_domain(property_counter, prop, info['domain']) + '\n'

                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectDomain'])
                                metric_info['shape'] = f'ex:CorrectDomainShape_{property_counter}'
                                metric_name = f'CorrectDomain_{property_counter}'
                                dq_results[metric_name] = metric_info

                                property_counter_map[property_counter] = prop
                                property_counter += 1

                        if info['range']:

                            count_datatype_range_props += 1
                            shacl_shapes += template.module.consistency_correct_range_datatype(property_counter, prop, info['range']) + '\n'
                            
                            metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectRangeDatatype'])
                            metric_info['shape'] = f'ex:CorrectRangeDatatypeShape_{property_counter}'
                            metric_name = f'CorrectRangeDatatype_{property_counter}'
                            dq_results[metric_name] = metric_info

                            property_counter_map[property_counter] = prop
                            property_counter += 1

                            shacl_shapes += template.module.syntactic_validity_incompatible_datatype(property_counter, prop, info['range']) + '\n'
                            
                            metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MemberIncompatibleDatatype'])
                            metric_info['shape'] = f'ex:MemberIncompatibleDatatypeShape_{property_counter}'
                            metric_name = f'MemberIncompatibleDatatype_{property_counter}'
                            dq_results[metric_name] = metric_info
                            
                            property_counter_map[property_counter] = prop
                            property_counter += 1

                            datatype = info['range']
                            regex_pattern = REGEX_PATTERNS_DICT[datatype] if datatype in REGEX_PATTERNS_DICT else None
                            
                            if regex_pattern:
                                shacl_shapes += template.module.syntactic_validity_malformed_datatype(property_counter, prop, regex_pattern) + '\n'
                        
                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MalformedDatatype'])
                                metric_info['shape'] = f'ex:MalformedDatatypeShape_{property_counter}'
                                metric_name = f'MalformedDatatype_{property_counter}'
                                dq_results[metric_name] = metric_info

                                property_counter_map[property_counter] = prop
                                property_counter += 1
                    else:
                        # In this case we don't filter properties that aren't used in the dataset
                        # since we want to check the correct usage of properties (that they are not used as a class)
                        shacl_shapes +=  template.module.consistency_misuse_properties(property_counter, prop, self.type_property) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MisplacedProperties'])
                        metric_info['shape'] = f'ex:MisplacedPropertiesShape_{property_counter}'
                        metric_name = f'MisplacedProperties_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

            if len(vocab_profile['irreflexive']) > 0:
                for prop in vocab_profile['reflexive']:
                    
                    if prop in properties_in_dataset:
                        count_irreflexive_props += 1
                        
                        shacl_shapes +=  template.module.consistency_irreflexive_property(property_counter, prop) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['IrreflexiveProperty'])
                        metric_info['shape'] = f'ex:IrreflexivePropertyShape_{property_counter}'
                        metric_name = f'IrreflexiveProperty_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

            if len(vocab_profile['inverse_functional']) > 0:
                for prop in vocab_profile['inverse_functional']:

                    if prop in properties_in_dataset:
                        count_inverse_functional_props += 1
                        
                        shacl_shapes +=  template.module.consistency_inverse_functional_property(property_counter, prop) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['InverseFunctionalProperty'])
                        metric_info['shape'] = f'ex:InverseFunctionalPropertyShape_{property_counter}'
                        metric_name = f'InverseFunctionalProperty_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

            if len(vocab_profile['functional']) > 0:
                for prop in vocab_profile['functional']:

                    if prop in properties_in_dataset:
                        count_functional_props += 1

                        shacl_shapes +=  template.module.consistency_functional_property(property_counter, prop) + '\n'
                        
                        metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['FunctionalProperty'])
                        metric_info['shape'] = f'ex:FunctionalPropertyShape_{property_counter}'
                        metric_name = f'FunctionalProperty_{property_counter}'
                        dq_results[metric_name] = metric_info

                        property_counter_map[property_counter] = prop
                        property_counter += 1

            if len(vocab_profile['deprecated_classes']) > 0:
                classes_list = " ".join([f"<{v}>" for v in vocab_profile['deprecated_classes']])
                shacl_shapes += template.module.consistency_deprecated_classes(classes_list, self.type_property) + '\n'
                
                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['DeprecatedClassesUsage'])
                metric_info['shape'] = f'ex:DeprecatedClassesUsageShape'
                metric_name = f'DeprecatedClassesUsage'
                dq_results[metric_name] = metric_info

                count_deprecated_classes = len(classes_list)

            if len(vocab_profile['deprecated_properties']) > 0:
                properties_list = " ".join([f"<{v}>" for v in vocab_profile['deprecated_properties']])
                
                shacl_shapes_inf += template.module.consistency_deprecated_properties(properties_list, self.type_property) + '\n'
                
                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['DeprecatedPropertiesUsage'])
                metric_info['shape'] = f'ex:DeprecatedPropertiesUsageShape'
                metric_name = f'DeprecatedPropertiesUsage'
                dq_results[metric_name] = metric_info

                count_deprecated_properties = len(properties_list)

            if len(vocab_profile['rdf_properties']) > 0:
                # In this case we don't filter properties that aren't used in the dataset
                # since we want to check the correct usage of properties (that they are not used as a class)
                for prop, info in vocab_profile['rdf_properties'].items():

                    shacl_shapes += template.module.consistency_misuse_properties(property_counter, prop, self.type_property) + '\n'
                    
                    metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MisplacedProperties'])
                    metric_info['shape'] = f'ex:MisplacedPropertiesShape_{property_counter}'
                    metric_name = f'MisplacedProperties_{property_counter}'
                    dq_results[metric_name] = metric_info

                    property_counter_map[property_counter] = prop
                    property_counter += 1

                    if prop in properties_in_dataset:

                        if info['domain']:
                            # only consider specific classes
                            if info['domain'] != 'http://www.w3.org/2002/07/owl#Thing':
                                shacl_shapes += template.module.consistency_correct_domain(property_counter, prop, info['domain']) + '\n'
                                
                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectDomain'])
                                metric_info['shape'] = f'ex:CorrectDomainShape_{property_counter}'
                                metric_name = f'CorrectDomain_{property_counter}'
                                dq_results[metric_name] = metric_info

                                property_counter_map[property_counter] = prop
                                property_counter += 1

                        if info['range']:
                            if info['range']['type'] == 'literal':
                                
                                count_datatype_range_props += 1
                                
                                shacl_shapes += template.module.consistency_correct_range_datatype(property_counter, prop, info['range']['value']) + '\n'
                                
                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectRangeDatatype'])
                                metric_info['shape'] = f'ex:CorrectRangeDatatypeShape_{property_counter}'
                                metric_name = f'CorrectRangeDatatype_{property_counter}'
                                dq_results[metric_name] = metric_info
                                
                                property_counter_map[property_counter] = prop
                                property_counter += 1

                                shacl_shapes += template.module.syntactic_validity_incompatible_datatype(property_counter, prop, info['range']['value']) + '\n'
                                
                                metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MemberIncompatibleDatatype'])
                                metric_info['shape'] = f'ex:MemberIncompatibleDatatypeShape_{property_counter}'
                                metric_name = f'MemberIncompatibleDatatype_{property_counter}'
                                dq_results[metric_name] = metric_info
                                
                                property_counter_map[property_counter] = prop
                                property_counter += 1

                                datatype = info['range']['value']
                                regex_pattern = REGEX_PATTERNS_DICT[datatype] if datatype in REGEX_PATTERNS_DICT else None
                                
                                if regex_pattern:
                                    shacl_shapes += template.module.syntactic_validity_malformed_datatype(property_counter, prop, regex_pattern) + '\n'
                            
                                    metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['MalformedDatatype'])
                                    metric_info['shape'] = f'ex:MalformedDatatypeShape_{property_counter}'
                                    metric_name = f'MalformedDatatype_{property_counter}'
                                    dq_results[metric_name] = metric_info

                                    property_counter_map[property_counter] = prop
                                    property_counter += 1

                            else:
                                # only consider specific classes
                                if info['range']['value'] != 'http://www.w3.org/2002/07/owl#Thing':
                                    count_object_range_props += 1
                                    shacl_shapes += template.module.consistency_correct_range_object(property_counter, prop, info['range']['value']) + '\n'
                                    
                                    metric_info = copy.deepcopy(DQ_MEASURES_DATA_SPECIFIC['CorrectRangeObject'])
                                    metric_info['shape'] = f'ex:CorrectRangeObjectShape_{property_counter}'
                                    metric_name = f'CorrectRangeObject_{property_counter}'
                                    dq_results[metric_name] = metric_info

                                    property_counter_map[property_counter] = prop
                                    property_counter += 1

        # Add number of owl:DatatypeProperty and owl:ObjectProperty
        graph_profile['count_owl_graph_profiletype_properties'] = count_dt_props_dataset
        graph_profile['count_owl_object_properties'] = count_o_props_dataset

        # Add number of properties with datatype range and object range
        graph_profile['count_object_range_props'] = count_object_range_props
        graph_profile['count_datatype_range_props'] = count_datatype_range_props

        # Add number of irreflexive properties
        graph_profile['count_irreflexive_props'] = count_irreflexive_props

        # Add number of inverse-functional properties
        graph_profile['count_inverse_functional_props'] = count_inverse_functional_props

        # Add number of functional properties
        graph_profile['count_functional_props'] = count_functional_props

        # Add number of dperecated classes
        graph_profile['count_deprecated_classes'] = count_deprecated_classes

        # Add number of deprecated properties
        graph_profile['count_deprecated_properties'] = count_deprecated_properties
        
        # Update profile with new information from vocabularies
        with open(f'{PROFILE_DATASETS_FOLDER_PATH}/{self.dataset_name}.json', 'w', encoding='utf-8') as f:
            json.dump(graph_profile, f, indent=4)

        # Save the DQ "initial" results for the shapes that need instantiation from vocabularies
        file_path = DQ_MEASURES_DATA_SPECIFIC_TEMPLATE_FILE_PATH
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dq_results, f, indent=4)

        return shacl_shapes, graph_profile, property_counter_map, class_counter_map

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