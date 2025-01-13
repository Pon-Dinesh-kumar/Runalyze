import os
import streamlit as st
from streamlit_echarts import st_echarts
import requests
from dotenv import load_dotenv
import this

st.set_page_config(layout="wide")
load_dotenv('access.env')
st.title("Azure DevOps Test Run Analysis")
cols = st.columns(8)


def initialize(run_id):
    #GETTING RUN RESULT
    url = f"https://dev.azure.com/MDTProductDevelopment/carelink/_apis/test/Runs/{run_id}/results?api-version=5.0"
    access_token = os.getenv('ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.ok:
        this.run_result = response.json()
    else:
        this.run_result = {}

    #GETTING RUN SUMMARY
    url = f"https://dev.azure.com/MDTProductDevelopment/carelink/_apis/test/Runs/{run_id}?api-version=5.0"
    response = requests.get(url, headers=headers, verify=False)
    if response.ok:
        this.run_summary = response.json()
    else:
        this.run_summary = {}

    #SETTING GLOBAL VARIABLES
    this.run_name = this.run_summary.get("name", "N/A")
    this.run_url = this.run_summary.get("url", "#")
    this.build_name = this.run_summary.get("build", {}).get("name", "N/A")
    this.build_url = this.run_summary.get("build", {}).get("url", "#")
    this.state = this.run_summary.get("state", "N/A")
    this.start_date = this.run_summary.get("startedDate", "N/A")
    this.end_date = this.run_summary.get("completedDate", "N/A")
    this.release_stage = this.run_summary.get("releaseEnvironmentUri", "N/A")
    this.total = this.run_summary.get("totalTests", 0)
    this.passed = this.run_summary.get("passedTests", 0)
    this.failed = next(
        (stat.get("count", 0) for stat in this.run_summary.get("runStatistics", []) if stat.get("outcome") == "Failed"), 0)
    this.aborted = next(
        (stat.get("count", 0) for stat in this.run_summary.get("runStatistics", []) if stat.get("outcome") == "None"), 0)



def custom_metric(label, value, color, font_size="16px"):
    return f"""
    <div style="border:2px solid {color}; border-radius:10px; padding:10px; margin:5px;">
        <h2 style="color:{color}; font-size:{font_size}; margin:0; line-height:1.2; padding: 0;">{label}</h2>
        <h1 style="color:{color}; font-size:calc({font_size} * 2); margin:0; line-height:1.2; padding: 0;">{value}</h1>
    </div>
    """

def classify_error_message(error_message):
    for class_label, keywords in this.class_keywords.items():
        if any(keyword in error_message for keyword in keywords):
            return class_label
    this.unclassified_errors.append(error_message)
    return "Unclassified"


def display_run_details():
    font_size = 14

    custom_css = f"""
    <style>
        .metric-container {{
            background-color: rgba(50, 50, 50, 0.7);
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .metric-label {{
            font-size: {font_size}px;
            font-weight: 200;
            color: #A9A9A9;
        }}
        .metric-value {{
            font-size: {int(font_size * 1.25)}px;
            margin-bottom: 0.75rem;
            color: #fff;
        }}
        .metric-link {{
            font-size: {int(font_size * 1.25)}px;
            margin-bottom: 0.75rem;
        }}
        .metric-link a {{
            color: #007bff;
            text-decoration: underline;
        }}
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Run ID</div>
            <div class="metric-value">{this.run_id}</div>
            <div class="metric-label">Run Name</div>
            <div class="metric-link"><a href="{this.run_url}" target="_blank">{this.run_name}</a></div>
            <div class="metric-label">Build Name</div>
            <div class="metric-link"><a href="{this.build_url}" target="_blank">{this.build_name}</a></div>
            <div class="metric-label">State</div>
            <div class="metric-value">{this.state}</div>
            <div class="metric-label">Start Date</div>
            <div class="metric-value">{this.start_date}</div>
            <div class="metric-label">End Date</div>
            <div class="metric-value">{this.end_date}</div>
            <div class="metric-label">Release Stage</div>
            <div class="metric-link"><a href="{this.release_stage}" target="_blank">{this.release_stage}</a></div>
        </div>
    """, unsafe_allow_html=True)


def analyze_and_plot():

    with cols[4]:
        st.markdown(custom_metric("Total Tests", this.total, "grey", "14px"), unsafe_allow_html=True)
    with cols[5]:
        st.markdown(custom_metric("Passed Tests", this.passed, "green", "14px"), unsafe_allow_html=True)
    with cols[6]:
        st.markdown(custom_metric("Failed Tests", this.failed, "red", "14px"), unsafe_allow_html=True)
    with cols[7]:
        st.markdown(custom_metric("Aborted Tests", this.aborted, "orange", "14px"), unsafe_allow_html=True)

    classification_counts = {key: 0 for key in this.class_keywords.keys()}
    classification_counts["Unclassified"] = 0
    keyword_counts = {key: {kw: 0 for kw in keywords} for key, keywords in this.class_keywords.items()}

    for result in this.run_result.get('value', []):
        outcome = result.get('outcome', None)
        if outcome == "Failed":
            error_message = result.get('errorMessage', '')
            class_label = classify_error_message(error_message)
            classification_counts[class_label] += 1

            for keyword in keyword_counts.get(class_label, {}):
                if keyword in error_message:
                    keyword_counts[class_label][keyword] += 1

    chart_data = [{"value": count, "name": f"{label} ({count})"} for label, count in classification_counts.items()]

    option_pie = {
        "title": {
            "text": "Failure Classification",
            "subtext": f"Run ID: {this.run_id}",
            "left": "center",
            "textStyle": {"color": "#FFFFFF", "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {d}%"
        },
        "legend": {
            "orient": "vertical",
            "left": "right",
            "textStyle": {
                "color": "#FFFFFF",
                "fontSize": 10
            },
            "backgroundColor": "rgba(50, 50, 50, 0.7)",
            "borderRadius": 5,
            "padding": [10, 10, 10, 10]
        },
        "series": [
            {
                "name": "Error Classification",
                "type": "pie",
                "radius": "50%",
                "data": chart_data,
                "label": {
                    "normal": {
                        "textStyle": {
                            "color": "#FFFFFF",
                            "fontWeight": "bold"
                        }
                    }
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    pie_chart_container = st.container()
    with pie_chart_container:
        col1, col2 = st.columns([2, 3])
        with col1:
            display_run_details()
        with col2:
            st_echarts(option_pie, height="600px")


    for class_label, keywords in keyword_counts.items():
        if any(keywords.values()):
            chart_data_bar = [{"value": count, "name": kw} for kw, count in keywords.items()]
            option_bar = {
                "title": {
                    "text": f"Keyword Distribution for {class_label}",
                    "left": "center",
                    "textStyle": {"color": "#FFFFFF", "fontWeight": "bold"}
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "shadow"
                    }
                },
                "grid": {
                    "left": "10%",
                    "right": "10%",
                    "bottom": "10%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "value",
                    "axisLabel": {"color": "#FFFFFF", "fontWeight": "bold"}
                },
                "yAxis": {
                    "type": "category",
                    "data": list(keywords.keys()),
                    "axisLabel": {
                        "color": "#FFFFFF",
                        "fontWeight": "bold",
                        "interval": 0,
                    }
                },
                "series": [
                    {
                        "data": chart_data_bar,
                        "type": "bar",
                        "itemStyle": {"color": "#61A0A8"},
                        "label": {
                            "show": True,
                            "position": "right",
                            "color": "#FFFFFF",
                            "fontWeight": "bold"
                        }
                    }
                ]
            }
            st_echarts(options=option_bar, key=class_label, height="500px")

    if this.unclassified_errors:
        st.subheader("Unclassified Errors:")
        for error in this.unclassified_errors:
            st.text(error)

with cols[0]:
    this.run_id = st.text_input("Enter the run ID:")
if st.button("Analyze"):
    initialize(this.run_id)
    analyze_and_plot()