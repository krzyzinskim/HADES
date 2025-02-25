import json
from copy import deepcopy
from typing import List

import click
import numpy as np
import pandas as pd
import spacy
import streamlit as st
from annotated_text import annotated_text

from config import Config
from utils import (calculate_distance_matrix, calculate_linkage_matrix,
                    get_hdbscan_clusters, get_hierarchical_clusters,
                    get_kmeans_clusters, manova_significant_difference_pval,
                    plot_clusters, plot_correlation_heatmap, plot_map,
                    plot_topic_distribution_radar,
                    plot_topic_distribution_violinplot, plot_topics)


@st.cache
def load_df_data(df_file_name: str, index_col=False) -> pd.DataFrame:
    return pd.read_csv(df_file_name, index_col=index_col)


@st.cache
def load_df_mapping_data(df_file_name: str, index_col=False) -> pd.DataFrame:
    return pd.read_csv(df_file_name, index_col=index_col)


@st.cache
def load_df_keywords_data(df_file_name: str, index_col=False) -> pd.DataFrame:
    return pd.read_csv(df_file_name, index_col=index_col)


@st.cache
def load_additional_dfs(additional_files_paths: List[str]) -> dict:
    return {
        path.split("/")[-1]:pd.read_csv(path, index_col=0)
        for path in additional_files_paths
    }


@st.cache
def load_summaries(file_path: str) -> json:
    f = open(file_path)
    j = json.load(f)
    f.close()
    return j


@st.cache
def load_essentials(file_path: str) -> json:
    f = open(file_path)
    j = json.load(f)
    f.close()
    return j


def main():
    config_path = "app_settings_necps.json"
    config = Config(config_path)
    if 'en' not in st.session_state:
            st.session_state.en =  spacy.load('en_core_web_sm')

    st.markdown(
        f"""
        <style>
            .streamlit-expanderHeader{{
                font-size: calc(1.2rem + 1.2vw);
                font-family: "Source Sans Pro", sans-serif;
                font-weight: 600;
                color: rgb(22, 14, 59);
                letter-spacing: -0.005em;
                line-height: 1.2;
            }}
            .css-12oz5g7{{
                max-width: 100%;
                padding: 5%;
            }}
            .css-vxbmln{{
                width: 244px;
            }}
            .imp_word{{
                color: blue;
            }}
            .css-1bn4mii{{
                transform: scale(0.93);
                margin-left: -50px;
            }}
            .css-19plaz0{{
                transform: scale(0.93);
                margin-left: -50px;
            }}
            .css-2lnqt{{
                transform: scale(0.93);
                margin-left: -50px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


    st.markdown("# Welcome to HADES!")
    st.markdown("#### Homologous Automated Document Exploration and Summarization - A powerful tool for comparing similarly structured documents")
    st.markdown(
        """
        On the left-hand side of the screen, you can select from different sections to access a range of options for data mapping, clustering, and metrics. Click on this link to learn more about our methods.

        Take a look at the plot below to see the results of our clustering analysis. The number of clusters shows you how we group your documents, and the MANOVA p value indicates the quality of the grouping. A p value lower than 0.05 is considered a good result.

        Are you ready to start comparing your documents in a whole new way? Let's get started with HADES! 🤗

        """
    )

    with st.sidebar:
        selected_section = st.selectbox("Select section", config.sections, index=0)
        topics_load = load_df_data(config.settings_dict["sections"][selected_section]["probs"])
        mapping_load = load_df_mapping_data(config.settings_dict["sections"][selected_section]["mapping"])
        keywords_load = load_df_keywords_data(
            config.settings_dict["sections"][selected_section]["topic_words"]
        )
        essentials_load = load_essentials(
            config.settings_dict["sections"][selected_section]["essentials"]
        )
        summaries_load = load_summaries(config.settings_dict["summaries_file"])

        topics = deepcopy(topics_load)
        mapping = deepcopy(mapping_load)
        keywords = deepcopy(keywords_load)
        essential_sentences = deepcopy(essentials_load)
        summaries = deepcopy(summaries_load)
        n_topics = len(topics.columns[1:])
        topic_names = topics.columns[1:]
        topic_matrix = topics.iloc[:, 1:].values

        selected_mapping = st.selectbox(
            "Select mapping",
            config.mappings,
            index=0,
            help="Method for representation of documents on 2D plot based on their contents",
        )

        selected_clustering = st.selectbox(
            "Select clustering method",
            config.clusterings,
            index=0,
            help="Method used for grouping documents",
        )

        if selected_clustering == "Hierarchical":
            distance_metric = st.selectbox(
                "Select metric",
                config.metric_choices.keys(),
                format_func=lambda x: config.metric_choices[x],
                index=0,
                help="Metric for calculating distances between contents",
            )

            linkage_method = st.selectbox(
                "Select linkage algorithm",
                ["average", "single", "complete", "weighted"],
                index=0,
                help="Linkage scheme used for grouping documents",
            )

            linkage = calculate_linkage_matrix(
                topic_matrix,
                linkage_method,
                distance_metric,
            )

            t = st.slider(
                f"Select distance threshold",
                min_value=0.0,
                value=float(np.median(linkage[:, 2])),
                max_value=float(np.max(linkage[:, 2])),
                step=1e-5,
                format="%.5f",
                help="Distance threshold used for creating groups",
            )
            labels = get_hierarchical_clusters(linkage, t).astype(str)

        elif selected_clustering == "K-Means":
            n_clusters = st.number_input(
                f"Select number of clusters",
                min_value=2,
                value=4,
            )
            labels = get_kmeans_clusters(topic_matrix, n_clusters).astype(str)

        elif selected_clustering == "HDBSCAN":
            distance_metric = st.selectbox(
                "Select option",
                config.metric_choices.keys(),
                format_func=lambda x: config.metric_choices[x],
                index=0,
            )
            min_cluster_size = st.number_input(
                f"Select minimum cluster size",
                min_value=1,
                value=5,
            )
            min_samples = st.number_input(
                f"Select minimum number of samples",
                min_value=1,
                value=1,
            )
            cluster_selection_epsilon = st.number_input(
                f"Select distance threshold",
                min_value=0.0,
                value=0.0,
                step=1e-5,
                format="%.5f",
            )

            distance_matrix = calculate_distance_matrix(
                pd.DataFrame(topic_matrix),
                distance_metric,
            )

            labels = get_hdbscan_clusters(
                distance_matrix,
                min_cluster_size,
                min_samples,
                cluster_selection_epsilon,
            ).astype(str)

    x, y = ("c1", "c2") if selected_mapping == "tSNE" else ("u1", "u2")

    sc1, sc2 = st.columns([4, 1])
    with sc1:
        if config.countries_division:
            map_tab, clustering_tab = st.tabs(["Map", "Clustering"])
            with map_tab:
                st.plotly_chart(
                    plot_map(topics, mapping, labels),
                    config=config.default_config,
                    use_container_width=True,
                )
            with clustering_tab:
                st.plotly_chart(
                    plot_clusters(topics, mapping, labels, x, y),
                    config=config.default_config,
                    use_container_width=True,
                )
        else:
            st.plotly_chart(
                    plot_clusters(topics, mapping, labels, x, y, try_flags=False, text=config.id_column),
                    config=config.default_config,
                    use_container_width=True,
            )
    with sc2:
        st.markdown(f"""</br></br></br></br></br></br>""", unsafe_allow_html=True)
        st.metric("Number of clusters", len(np.unique(labels)))
        pval = manova_significant_difference_pval(
            topics.iloc[:, 1:], labels
        )
        if pval < 1e-6:
            pval = "<1e-6"
            st.metric("MANOVA p value", pval)
        else:
            st.metric(
                "MANOVA p value",
                "{:.6f}".format(round(pval, 6)),
            )
        if config.countries_division:
            st.markdown(f"""</br></br>""", unsafe_allow_html=True)


    st.markdown(
        """
        Below you can find three bookmarks: 
        - Document details will provide a summary of the selected section (left panel) for a given country. Then for each section topic, you can check the most important sentences; colored words mean there were essential in assigning topics. The higher the number next to the word, the more important it is. At the bottom of the page, you can compare multiple documents with each other. 
        - In the Topic details section, you will find an interactive topic map with relevant important words and keywords for each topic
        - Additional data comparison section shows comparison to data like geopolitical factors
        """
    )
    tabs = st.tabs(["Document details", "Topic details", "Additional data comparison"])


    with tabs[0]:
        selected_document = st.selectbox("Select document", sorted(topics[config.id_column].unique()), index=0)
        st.header(f"Document details: {selected_document}")

        st.markdown(f"""<h4 style="padding-top: 0px;">Section summary:</h4>""", unsafe_allow_html=True)
        st.write(summaries[selected_section][selected_document])
        st.markdown(f"""<hr style='margin: 0px;'>""", unsafe_allow_html=True)
        clean_topics = [topic_name.split(" ", 1)[1] for topic_name in topic_names]
        selected_topic = st.selectbox(
            "Select topic",
            clean_topics,
            index=0)
        topic_num = 0
        for idx, topic in enumerate(clean_topics):
            if selected_topic == topic:
                topic_num = idx
        st.markdown(f"""<h4 style="padding-top: 0px;">Essential sentences:</h4>""", unsafe_allow_html=True)
        ess_words = list(essential_sentences[selected_document][str(topic_num)]['words'].keys())
        for i in range(3):   
            ess_sentence = essential_sentences[selected_document][str(topic_num)]['sentences'][i][0]
            ess_sentence_splitted = ess_sentence.split()
            sentence = [f"{i+1}. "]
            for word in ess_sentence_splitted:
                word_en = st.session_state.en(word)
                is_imp = bool(word_en[0].lemma_ in ess_words)
                if is_imp:
                    sentence.append((
                        str(word),
                        str(np.round(100*essential_sentences[selected_document][str(topic_num)]['words'][word_en[0].lemma_], 2)),
                        "#afa"))
                else:
                    sentence.append(str(word + " "))
            annotated_text(*sentence)
            st.markdown(f"""</br>""", unsafe_allow_html=True)

        st.header(f"Compare documents")
        selected_entities = st.multiselect(
            label="Select document",
            options=sorted(topics[config.id_column].unique()),
            default=sorted(topics[config.id_column].unique())[:2],  # assumption that there are two entities
        )
        radar_col, topic_dist_col = st.columns(2)
        with radar_col:
            st.plotly_chart(
                plot_topic_distribution_radar(topics, selected_entities, app_format=True),
                config=config.default_config,
                use_container_width=True,
                width=500,
            )
            topic_names = np.hstack(topics.columns[1:])
            html_text_legend = "".join(["<span style='display: inline-block;'>T" + str(i+1) + ": " + topic_names[i] + "  &#x2022; </span>" for i in range(len(topic_names))])
            html_string = f"""
            <div style="border: 1px solid #808495;border-radius: 5px;padding: 10px;margin: 5px 20px; color: #808495;">
                {html_text_legend}
            </div>
            """
            st.markdown(html_string, unsafe_allow_html=True)
        with topic_dist_col:
            st.plotly_chart(
                plot_topic_distribution_violinplot(topics, selected_entities),
                config=config.default_config,
                use_container_width=True,
                width=500,
            )


    with tabs[1]:
        st.header("Topic analysis")
        with open(config.settings_dict["sections"][selected_section]["vis"], "r") as file:
            html_string = file.read()
        st.components.v1.html(
            html_string,
            width=1250,
            height=800,
            scrolling=False
        )
        st.header(f"Topic keywords")
        colors_list = [
            "#8bdcbe",
            "#f05a71",
            "#371ea3",
            "#46bac2",
            "#ae2c87",
            "#ffa58c",
            "#4378bf",
        ] * n_topics
        keywords_col1, keywords_col2 = st.columns(2)
        for i in range(n_topics):
            topic_num = i
            if i % 2:
                keywords_col2.pyplot(
                    plot_topics(
                        keywords,
                        i,
                        topic_num,
                        topic_names[topic_num],
                        colors_list[topic_num],
                    )
                )
            else:
                keywords_col1.pyplot(
                    plot_topics(
                        keywords,
                        i,
                        topic_num,
                        topic_names[topic_num],
                        colors_list[topic_num],
                    )
                )
        

    with tabs[2]:
        if len(config.settings_dict["additional_files"]) > 0:
            st.header("Correlation heatmap")
            heatmap_params_col, heatmap_plot_col = st.columns(2)
            with heatmap_params_col:
                topics_additional = topics.copy()
                topics_additional[config.id_column] = topics_additional[config.id_column].apply(
                    lambda x: x.lower()
                )
                num_topics = len(topics_additional.columns)-1
                selected_columns = st.multiselect(
                    "Select topic modelling columns",
                    list(topics_additional.columns[1:(num_topics+1)]),
                    default=list(topics_additional.columns[1:(num_topics+1)]), 
                )
                additional_dfs = load_additional_dfs(config.settings_dict["additional_files"])
                selected_data = st.selectbox(
                    "Select additional data",
                    list(additional_dfs.keys()),
                    index=0,
                )
                df_selected = deepcopy(additional_dfs[selected_data])
                df_selected[config.id_column] = df_selected[config.id_column].apply(lambda x: x.lower())
                default = list(df_selected.columns[1:])[0]
                
                selected_columns_additional = st.multiselect(
                    "Select additional data columns",
                    list(df_selected.columns[1:]),
                    default=default,
                )
                merged_df = topics_additional[selected_columns + [config.id_column]].merge(
                    df_selected[selected_columns_additional + [config.id_column]],
                    how="left",
                    on=config.id_column,
                )
                selected_method = st.selectbox(
                    "Select correlation method",
                    ["Pearson", "Kendall", "Spearman"],
                    index=0,
                )
                corr_df = merged_df.corr(method=selected_method.lower(), numeric_only=True)
                corr_df = corr_df.drop(selected_columns, axis=1)
                corr_df = corr_df.drop(selected_columns_additional, axis=0)
            with heatmap_plot_col:
                st.markdown(f"""</br></br></br>""", unsafe_allow_html=True)
                st.pyplot(plot_correlation_heatmap(corr_df))
        else:
            st.write("There aren't any additional files defined")
            st.write("Additional files can be defined in application settings")

if __name__ == '__main__':
    main()