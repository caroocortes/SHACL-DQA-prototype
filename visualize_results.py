import json
import streamlit as st
import os
from const import *
import pandas as pd
import plotly.graph_objects as go

def get_score_color(score):
    try:
        score = float(score)
    except Exception:
        return "black"  # fallback for non-numeric scores
    if score >= 0.95:
        return "green"
    elif score >= 0.7:
        return "orange"
    else:
        return "red"

def create_results_visualization(run_info):

    # --------------------------- 
    # Sidebar panel
    # --------------------------- 
    st.sidebar.title("")
    DATASETS_FOLDER_PATH = "datasets"
    datasets = [
        d for d in os.listdir(DATASETS_FOLDER_PATH)
        if (
            d != "vocabularies"
            and os.path.isdir(os.path.join(DATASETS_FOLDER_PATH, d, "results"))
        )
    ]
    if not datasets:
        st.error("No datasets found.")
        return

    selected_dataset = st.sidebar.selectbox("Select Dataset", datasets)
    dataset_name = selected_dataset
    
    csv_path = f'{DQ_ASSESSMENT_RESULTS_FOLDER_PATH.format(dataset_name=dataset_name)}dq_assessment_{dataset_name}.csv'
    if not os.path.exists(csv_path):
        st.error(f"No results CSV found for dataset '{dataset_name}'.")
        return
    
    df = pd.read_csv(csv_path)
    df['vocab'] = df['vocab'].fillna('')

    graph_profile = run_info[dataset_name].get('graph_profile', {})

    num_triples = graph_profile.get('num_triples', 0)
    num_properties = graph_profile.get('num_properties', 0)
    num_classes = graph_profile.get('num_classes', 0)
    num_entities = graph_profile.get('num_entities', 0)
    num_owl_datatype_props = graph_profile.get('count_owl_datatype_properties', 0)
    num_owl_object_props = graph_profile.get('count_owl_object_properties', 0)
    count_datatype_range_props = graph_profile.get('count_datatype_range_props', 0)
    count_object_range_props = graph_profile.get('count_object_range_props', 0)
    count_irreflexive_props = graph_profile.get('count_irreflexive_props', 0)
    count_inverse_functional_props = graph_profile.get('count_inverse_functional_props', 0)
    count_functional_props = graph_profile.get('count_functional_props', 0)
    num_classes_vocabularies = graph_profile.get('num_classes_vocabularies', 0)
    num_properties_vocabularies = graph_profile.get('num_properties_vocabularies', 0)
    num_properties_domain = graph_profile.get('num_properties_domain', 0)

    dimensions = sorted(df['dimension'].dropna().unique().tolist())
    selected_dimension = st.sidebar.selectbox("Select Dimension", dimensions)

    st.markdown(f"## DQ Assessment Results")

    dim_group = df[df['dimension'] == selected_dimension]
    st.markdown(f"**Dimension:** {selected_dimension}")

    last_vocab = ''
    for metric_id, group in dim_group.groupby('metric_id'):
        metric_name = group.iloc[0]['metric']

        last_vocab = ''
        with st.expander(f"**Metric:** {metric_name}"):
            counter = 0
            num_metrics = len(group)
            for idx, row in group.iterrows():
                if counter == 0 and num_metrics != 1:
                    st.markdown("---")
                    
                if 'vocab' in row and row['vocab'] != '' and last_vocab != row['vocab']:
                    last_vocab = row['vocab']
                    st.markdown(f"### Vocab: {row['vocab']}")
                st.markdown(f"**Description:** {row['metric_description']}")
                score = row['score']
                color = get_score_color(score)
                st.markdown(f"**Score:** <span style='color:{color}'>{round(score,3)}</span>", unsafe_allow_html=True)

                if 'meta_metric_calculation' in row and pd.notna(row['meta_metric_calculation']):
                    st.markdown(f"**Aggregation:** {row['meta_metric_calculation']}")
                else:
                    st.markdown(f"**Metric calculation:** {row['metric_calculation']}")
                # if pd.notna(row["message"]):
                #     st.markdown(f"**Message:** {row['message']}")
                if 'violations' in row and pd.notna(row['violations']) and str(row['violations']).strip():
                    st.markdown(f"**Violations ({row['num_violations']}):** ")
                    st.markdown(f"*Individual score:* {row['metric_calculation']}")
                    # Split violations by ';', show only the first 100
                    violations_list = [v.strip() for v in str(row['violations']).split(';') if v.strip()]
                    first_100 = violations_list[:100]
                    st.markdown(
                        f"""
                        <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 8px; background: #f9f9f9; border-radius: 10px;">
                            <pre style="margin: 0;">{";\n".join(first_100)}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if len(violations_list) > 100:
                        st.info(f"Showing first 100 of {len(violations_list)} violations.")

                st.markdown(f"**Inference:** {row['inference']}")
                st.markdown("**Shape template:**")
                st.code(f"{row['shape_template'].encode('utf-8').decode('unicode_escape')}")
                
                counter += 1
                if counter < num_metrics:
                    st.markdown("---")

    st.markdown(f"## Statistics")
    st.markdown(f"**Dataset:** {dataset_name}")
    st.markdown("**Dataset Statistics**")
    stats = {
        "Number of triples": num_triples,
        "Number of entities": num_entities,
        "Number of classes": num_classes,
        "Number of properties": num_properties,
    }
    if num_owl_datatype_props > 0:
        stats["Number of owl:DatatypeProperty"] = num_owl_datatype_props
    if num_owl_object_props > 0:
        stats["Number of owl:ObjectProperty"] = num_owl_object_props
    if count_datatype_range_props > 0:
        stats["Properties with datatype range"] = count_datatype_range_props
    if count_object_range_props > 0:
        stats["Properties with object range"] = count_object_range_props
    if num_properties_domain > 0:
        stats["Properties with defined domain"] = num_properties_domain
    if count_inverse_functional_props > 0:
        stats["Inverse-functional properties"] = count_inverse_functional_props
    if count_functional_props > 0:
        stats["Functional properties"] = count_functional_props
    if count_irreflexive_props > 0:
        stats["Irreflexive properties"] = count_irreflexive_props
    if num_properties_vocabularies > 0:
        stats["Properties defined in vocabularies"] = num_properties_vocabularies
    if num_classes_vocabularies > 0:
        stats["Classes defined in vocabularies"] = num_classes_vocabularies

    st.table(pd.DataFrame(list(stats.items()), columns=["Statistic", "Value"]).set_index('Statistic'))

    num_metrics = int(len(df['metric'].unique()))
    
    def format_elapsed_time(seconds):
        if seconds < 60:
            return f"{round(seconds, 2)}", "(s)"
        else:
            return f"{round(seconds / 60, 2)}", "(m)"

    total_time_text, total_time_unit = format_elapsed_time(run_info[dataset_name]['total_elapsed_time'])
    vocab_time_text, vocab_time_unit = format_elapsed_time(run_info[dataset_name]['vocab_shapes_elapsed_time'])
    data_time_text, data_time_unit = format_elapsed_time(run_info[dataset_name]['data_shapes_elapsed_time'])
    metadata_time_text, metadata_time_unit = format_elapsed_time(run_info[dataset_name]['metadata_shapes_elapsed_time'])
    inference_time_text, inference_time_unit = format_elapsed_time(run_info[dataset_name]['inference_shapes_elapsed_time'])

    dq_stats = {
        f"Total validation time {total_time_unit}": total_time_text,
        f"Vocab shapes validation time {vocab_time_unit}": vocab_time_text,
        f"Data shapes validation time {data_time_unit}": data_time_text,
        f"Metadata shapes validation time {metadata_time_unit}": metadata_time_text,
        f"Inference shapes validation time {inference_time_unit}": inference_time_text,
        "Number of metrics": num_metrics,
        "Number of shapes": run_info[dataset_name]["num_inst_shapes"], 
    }

    # Data Quality Assessment statistics
    st.markdown("**Data Quality Assessment**")
    st.table(pd.DataFrame([(k, str(v)) for k, v in dq_stats.items()], columns=["Statistic", "Value"]).set_index("Statistic"))

    # Metric coverage
    
    labels = ["Covered fully", "Covered partial", "Not covered"]

    # TODO: ACTUALIZAR CUANDO TENGA LA DE SPATIAL DATA
    shacl_core_values = [21, 21, 26]
    shacl_inference_values = [22, 20, 26]

    fig = go.Figure()

    # SHACL core donut
    fig.add_trace(go.Pie(
        labels=labels, 
        values=shacl_core_values, 
        name="SHACL core",
        hole=0.5,
        domain={'x': [0, 0.48]},
        hoverinfo="label+percent+value",
        textinfo='percent+label'
    ))

    # SHACL core + inference donut
    fig.add_trace(go.Pie(
        labels=labels, 
        values=shacl_inference_values,
        name="SHACL core + inference",
        hole=0.5,
        domain={'x': [0.52, 1]},
        hoverinfo="label+percent+value",
        textinfo='percent+label'
    ))

    fig.update_layout(
        title_text="SHACL Coverage Comparison",
        annotations=[
            dict(text='SHACL core', x=0.20, y=0.5, font_size=14, showarrow=False),
            dict(text='SHACL core + inference', x=0.8, y=0.5, font_size=14, showarrow=False)
        ],
        showlegend=False
    )
    st.markdown("### Metric coverage")
    st.plotly_chart(fig)

    dq_data = [
        ["Availability", "A1", "Accessibility of the SPARQL endpoint and the server", "No", "No"],
        ["Availability", "A2", "Accessibility of the RDF dumps", "Partial", "Partial"],
        ["Availability", "A3", "Dereferenceability of the URI", "No", "No"],
        ["Availability", "A4", "No misreported content types", "No", "No"],
        ["Availability", "A5", "Dereferenced forward-links", "No", "No"],
        ["Licensing", "L1", "Machine-readable indication of the license in the VoID description of the dataset", "Yes", "Yes"],
        ["Licensing", "L2", "Human-readable indication of the license in the documentation of the dataset", "No", "No"],
        ["Licensing", "L3", "Specifying the correct license", "No", "No"],
        ["Interlinking", "I1", "Detection of good quality interlinks", "No", "No"],
        ["Interlinking", "I2", "Existence of links to external data providers", "Yes", "Yes"],
        ["Interlinking", "I3", "Dereferenced back-links", "No", "No"],
        ["Security", "SE1", "Usage of digital signatures", "Yes", "Yes"],
        ["Security", "SE2", "Authenticity of the dataset", "Yes", "Yes"],
        ["Performance", "P1", "Usage of slash-URIs", "Yes", "Yes"],
        ["Performance", "P2", "Low latency", "No", "No"],
        ["Performance", "P3", "High throughput", "No", "No"],
        ["Performance", "P4", "Scalability of a data source", "No", "No"],
        ["Relevancy", "R1", "Relevant terms within meta-information attributes", "No", "No"],
        ["Relevancy", "R2", "Coverage", "Partial", "Partial"],
        ["Understandability", "U1", "Human-readable labelling of classes, properties and entities as well as presence of metadata", "Partial", "Partial"],
        ["Understandability", "U2", "Indication of one or more exemplary URIs", "Yes", "Yes"],
        ["Understandability", "U3", "Indication of a regular expression that matches the URIs of a dataset", "Yes", "Yes"],
        ["Understandability", "U4", "Indication of an exemplary SPARQL query", "No", "No"],
        ["Understandability", "U5", "Indication of the vocabularies used in the dataset", "Yes", "Yes"],
        ["Understandability", "U6", "Provision of message boards and mailing lists", "No", "No"],
        ["Trustworthiness", "T1", "Trustworthiness of statements", "No", "No"],
        ["Trustworthiness", "T2", "Trustworthiness through reasoning", "Partial", "Partial"],
        ["Trustworthiness", "T3", "Trustworthiness of statements, datasets and rules", "Partial", "Partial"],
        ["Trustworthiness", "T4", "Trustworthiness of a resource", "No", "No"],
        ["Trustworthiness", "T5", "Trustworthiness of the information provider", "Partial", "Partial"],
        ["Trustworthiness", "T6", "Trustworthiness of information provided (content trust)", "Yes", "Yes"],
        ["Trustworthiness", "T7", "Reputation of the dataset", "No", "No"],
        ["Timeliness", "TI1", "Freshness of datasets based on currency and volatility", "Partial", "Partial"],
        ["Timeliness", "TI2", "Freshness of datasets based on their data source", "Partial", "Partial"],
        ["Representational conciseness", "RC1", "Keeping URIs short", "Yes", "Yes"],
        ["Representational conciseness", "RC2", "No use of prolix RDF features", "Yes", "Yes"],
        ["Interoperability", "IO1", "Re-use of existing terms", "Yes", "Yes"],
        ["Interoperability", "IO2", "Re-use of existing vocabularies", "Partial", "Partial"],
        ["Versatility", "V1", "Provision of the data in different serialization formats", "Yes", "Yes"],
        ["Versatility", "V2", "Checking whether data is available in different languages", "Yes", "Yes"],
        ["Interpretability", "IP1", "Use of self-descriptive formats", "Yes", "Yes"],
        ["Interpretability", "IP2", "Detecting the interpretability of data", "Partial", "Partial"],
        ["Interpretability", "IP3", "Invalid usage of undefined classes and properties", "Yes", "Yes"],
        ["Interpretability", "IP4", "No misinterpretation of missing values", "Partial", "Partial"],
        ["Syntactic validity", "SV1", "No syntax errors of the documents", "No", "No"],
        ["Syntactic validity", "SV2", "Syntactically accurate values", "Partial", "Partial"],
        ["Syntactic validity", "SV3", "No malformed datatype literals", "Yes", "Yes"],
        ["Semantic accuracy", "SA1", "No outliers", "No", "No"],
        ["Semantic accuracy", "SA2", "No inaccurate values", "Partial", "Partial"],
        ["Semantic accuracy", "SA3", "No inaccurate annotations, labellings or classifications", "Partial", "Partial"],
        ["Semantic accuracy", "SA4", "No misuse of properties", "No", "No"],
        ["Semantic accuracy", "SA5", "Detection of valid rules", "No", "No"],
        ["Consistency", "C1", "No use of entities as members of disjoint classes", "Yes", "Yes"],
        ["Consistency", "C2", "No misplaced classes or properties", "No", "No"],
        ["Consistency", "C3", "No misuse of owl:DatatypeProperty or owl:ObjectProperty", "Yes", "Yes"],
        ["Consistency", "C4", "Members of owl:DeprecatedClass or owl:DeprecatedProperty not used", "Partial", "Yes"],
        ["Consistency", "C5", "Valid usage of inverse-functional properties", "Partial", "Partial"],
        ["Consistency", "C6", "Absence of ontology hijacking", "No", "No"],
        ["Consistency", "C7", "No negative dependencies/correlation among properties", "Yes", "Yes"],
        ["Consistency", "C8", "No inconsistencies in spatial data", "?", "?"],
        ["Consistency", "C9", "Correct domain and range definition", "Yes", "Yes"],
        ["Consistency", "C10", "No inconsistent values", "Partial", "Partial"],
        ["Conciseness", "CO1", "High intensional conciseness", "No", "No"],
        ["Conciseness", "CO2", "High extensional conciseness", "Partial", "Partial"],
        ["Conciseness", "CO3", "Usage of unambiguous annotations/labels", "No", "No"],
        ["Completeness", "CM1", "Schema completeness", "Partial", "Partial"],
        ["Completeness", "CM2", "Property completeness", "Partial", "Partial"],
        ["Completeness", "CM3", "Population completeness", "No", "No"],
        ["Completeness", "CM4", "Interlinking completeness", "Partial", "Partial"],
    ]

    # Data for the table
    coverage_data = {
        "SHACL Version": ["SHACL core", "SHACL core + inference"],
        "Covered fully": [21, 22],
        "Covered partial": [21, 20],
        "Not covered": [26, 26]
    }

    coverage_df = pd.DataFrame(coverage_data).set_index("SHACL Version")
    st.table(coverage_df)

    df_dq = pd.DataFrame(
        dq_data,
        columns=["Dimension", "Metric Id", "Metric", "SHACL core", "SHACL core with inference"]
    ).set_index('Dimension')

    st.dataframe(df_dq, use_container_width=True)

    
def visualize_results():
    with open("run_info.json", "r", encoding="utf-8") as f:
        run_info = json.load(f)
    create_results_visualization(run_info)

if "__main__":

    visualize_results()