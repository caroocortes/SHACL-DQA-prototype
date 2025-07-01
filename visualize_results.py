import json
import streamlit as st
import os
from const import *
import pandas as pd
import plotly.graph_objects as go
from const import METRIC_COVERAGE, BINARY_METRICS_METADATA

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

def show_dq_assessment_results(df):

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

                if ((row['shape_name'].removesuffix("Shape") in BINARY_METRICS_METADATA) or (row['shape_name'].startswith('Authenticity'))) and row['score'] < 1 :
                    st.markdown(f"**Message:** {row['message']} ")

                elif 'violations' in row and pd.notna(row['violations']) and str(row['violations']).strip():
                    st.markdown(f"**Violations ({row['num_violations']}):** ")
                
                    if pd.notna(row['meta_metric_calculation']):
                        st.markdown(f"*Individual score:* {row['metric_calculation']}")
                    
                    # Split violations by ';', show only the first 100
                    violations_list = [v.strip() for v in str(row['violations']).split(';') if v.strip()]
                    first_100 = violations_list[:100]
                    st.markdown(
                        f"""
                        <div style="max-height: 200px; max-width: 1000px; overflow-y: auto; border: 1px solid #ddd; padding: 8px; background: #f9f9f9; border-radius: 10px;">
                            <pre style="margin: 0;">{";\n".join(first_100)}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if len(violations_list) > 100:
                        st.info(f"Showing first 100 of {len(violations_list)} violations.")
                
                st.markdown("**Shape template:**")
                if pd.notnull(row['shape_template']):
                    st.code(str(row['shape_template']).encode('utf-8').decode('unicode_escape'))
                    
                counter += 1
                if counter < num_metrics:
                    st.markdown("---")

def show_dq_assessment_statistics(run_info, dataset_name, df):
    """ 
        Displays DQA statistics
    """

    graph_profile = run_info[dataset_name].get('graph_profile', {})

    num_triples = graph_profile.get('num_triples', 0)
    num_properties = graph_profile.get('num_properties', 0)
    num_classes = graph_profile.get('num_classes', 0)
    num_entities = graph_profile.get('num_entities', 0)
    num_entities_with_interlinking = graph_profile.get('num_entities_with_interlinking', 0)
    num_entities_label_property =  graph_profile.get('num_entities_label_property', 0)
    num_entities_description_property = graph_profile.get('num_entities_description_property', 0)
    num_owl_datatype_props = graph_profile.get('count_owl_datatype_properties', 0)
    num_owl_object_props = graph_profile.get('count_owl_object_properties', 0)
    count_range_props = graph_profile.get('count_range_props', 0)
    count_irreflexive_props = graph_profile.get('count_irreflexive_props', 0)
    count_inverse_functional_props = graph_profile.get('count_inverse_functional_props', 0)
    count_functional_props = graph_profile.get('count_functional_props', 0)
    num_classes_vocabularies = graph_profile.get('num_classes_vocabularies', 0)
    num_properties_vocabularies = graph_profile.get('num_properties_vocabularies', 0)
    num_properties_domain = graph_profile.get('num_properties_domain', 0)

    st.markdown(f"## Statistics")
    st.markdown(f"**Dataset:** {dataset_name}")
    st.markdown("**Dataset Statistics**")
    stats = {
        "Number of triples": num_triples,
        "Number of entities": num_entities,
        "Number of entities with labels": num_entities_label_property,
        "Number of entities with descriptions": num_entities_description_property,
        "Number of entities with interlinking property": num_entities_with_interlinking,
        "Number of classes used": num_classes,
        "Number of properties used": num_properties,
    }
    if num_owl_datatype_props > 0:
        stats["Number of owl:DatatypeProperty used"] = num_owl_datatype_props
    if num_owl_object_props > 0:
        stats["Number of owl:ObjectProperty used"] = num_owl_object_props
    if count_range_props > 0:
        stats["Number of properties used with a defined range"] = count_range_props
    if num_properties_domain > 0:
        stats["Number of properties used that have a defined domain"] = num_properties_domain
    if count_inverse_functional_props > 0:
        stats["Inverse-functional properties used"] = count_inverse_functional_props
    if count_functional_props > 0:
        stats["Functional properties used"] = count_functional_props
    if count_irreflexive_props > 0:
        stats["Irreflexive properties used"] = count_irreflexive_props
    if num_properties_vocabularies > 0:
        stats["Properties defined in vocabularies (includes deprecated ones)"] = num_properties_vocabularies
    if num_classes_vocabularies > 0:
        stats["Classes defined in vocabularies (includes deprecated ones)"] = num_classes_vocabularies

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
    dq_stats = {
        f"Total validation time {total_time_unit}": total_time_text,
        f"Metadata shapes validation time {metadata_time_unit}": metadata_time_text,
        f"Data shapes validation time {data_time_unit}": data_time_text,
        f"Vocabulary shapes validation time {vocab_time_unit}": vocab_time_text,
        "Number of metrics": num_metrics,
        "Number of shapes": run_info[dataset_name]["num_inst_shapes"], 
    }

    st.markdown("**Data Quality Assessment**")
    st.table(pd.DataFrame([(k, str(v)) for k, v in dq_stats.items()], columns=["Statistic", "Value"]).set_index("Statistic"))

def show_metric_coverage():
    st.markdown("### Metric coverage")
    st.markdown("**Total number of metrics:** 69")
    
    # Values for donut chart
    labels = ["Covered fully", "Covered partial", "Not covered"]
    shacl_core_values = [24, 19, 26]

    fig = go.Figure()

    # Donut chart
    fig.add_trace(go.Pie(
        labels=labels, 
        values=shacl_core_values, 
        name="SHACL core",
        hole=0.5,
        domain={'x': [0, 0.48]},
        hoverinfo="label+percent+value",
        textinfo='percent+label'
    ))

    fig.update_layout(
        title_text="",
        annotations=[
            dict(text='SHACL core', x=0.20, y=0.5, font_size=14, showarrow=False),
        ],
        showlegend=False
    )
    st.plotly_chart(fig)

    df_dq = pd.DataFrame(
        METRIC_COVERAGE,
        columns=["Dimension", "Metric Id", "Metric", "SHACL core"]
    ).set_index('Dimension')

    st.dataframe(df_dq, use_container_width=True)


def create_results_visualization(run_info):

    st.set_page_config(layout='wide')
    # --------------------------- 
    # Sidebar panel
    # --------------------------- 
    st.sidebar.title("")

    view_option = st.sidebar.selectbox("View", ["DQA Results", "Metric Coverage"])

    if view_option == "DQA Results":

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
    
        show_dq_assessment_results(df)
        show_dq_assessment_statistics(run_info, dataset_name, df)
        
    else:
        show_metric_coverage()
    
def visualize_results():
    with open("run_info.json", "r", encoding="utf-8") as f:
        run_info = json.load(f)
    create_results_visualization(run_info)

if "__main__":

    visualize_results()