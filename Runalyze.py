import streamlit as st
import requests
from streamlit_echarts import st_echarts


st.set_page_config(layout="wide")
st.title("Azure DevOps Test Run Analysis")
cols = st.columns(8)
 
class_keywords = { 
    "Selenium Exceptions": [
        "InvalidCastException", "InvalidOperationException", "NoSuchElementException",
        "NotImplementedException", "WebDriverTimeoutException", "NullReferenceException",
        "WebDriverException", "FormatException", "BindingException", "JsonReaderException",
        "TimeoutException", "AggregateException", "ComparisonException", "XmlException",
        "ElementNotInteractableException", "HttpRequestException", "NoSuchWindowException",
        "ArgumentNullException", "ApiException", "InvalidElementStateException", "StaleElementReferenceException",
        "DirectoryNotFoundException"
    ],
    "Custom Exceptions": [
        "Cities belonging to initiating clinic as well as Specialist clinics are displayed",
        "Data Export failed", "Unexpected page displayed", "No pull record found",
        "No commands available to post", "Collection was modified; enumeration operation may not execute",
        "Row with clinic name", "No patient with key 0 exists",
        "PDF generation failed", "No emails matching the search were found", "No clinic with key 0 exists",
        "Patient is not displayed on Patient Assignment page", "InstrumentCommandsResponse is null", "Transmission not found", "HeartFailureManagementLink does not exists",
        "No Archived Transmissions are displayed on the Transmissions List Page", "Tranmission with iTransmissionId", "Transmission not found",
        "Unable to retrieve EarliestAppointmentDate for patient", "Patient with DSN"
    ],
    "Assert Failed": [
        "Assert.IsTrue", "Assert.Fail", "Assert.AreEqual", "Assert.IsNotNull", "Assert.IsFalse", "StringAssert.Contains",
        "CollectionAssert.AreEquivalent", "Assert.Inconclusive"
    ],
    "Data Setup API Error": [
        "Data Setup API error InternalServerError (500)", "Data Setup API error Unauthorized (401)", "Data Setup API error NotFound (404)", "DataSetupService timedout" 
    ],
    "Carelink API Error": [
        "Carelink API error"
    ]
}

unclassified_errors = [] 

def classify_error_message(error_message):
    for class_label, keywords in class_keywords.items():
        if any(keyword in error_message for keyword in keywords):
            return class_label
    unclassified_errors.append(error_message)
    return "Unclassified"

def fetch_run_results(run_id):
    url = f"https://dev.azure.com/MDTProductDevelopment/carelink/_apis/test/Runs/{run_id}/results?api-version=5.0"
    headers = {
        'Authorization': f'Bearer {"3xdeeY8sHgnb7aBV26Fcrj8yNogN7MWv1bFagtzUih7MBpCdiOYYJQQJ99BAACAAAAA4nb4XAAASAZDOXTze"}',  
    }
    
    response = requests.get(url, headers=headers, verify=False)  
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to retrieve data for run ID {run_id}. Status Code: {response.status_code}")
        return None



def fetch_test_run_summary(run_id):
    url = f"https://dev.azure.com/MDTProductDevelopment/carelink/_apis/test/Runs/{run_id}?api-version=5.0"
    headers = {
        'Authorization': f'Bearer {"3xdeeY8sHgnb7aBV26Fcrj8yNogN7MWv1bFagtzUih7MBpCdiOYYJQQJ99BAACAAAAA4nb4XAAASAZDOXTze"}',
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        summary = response.json()
        return {
            "total": summary.get("totalTests", 0),
            "passed": summary.get("passedTests", 0),
            "failed": summary.get("runStatistics", [{}])[2].get("count", 0), 
            "aborted": summary.get("unanalyzedTests", 0) - summary.get("runStatistics", [{}])[2].get("count", 0)
        }
    else:
        st.error(f"Failed to retrieve summary for run ID {run_id}. Status Code: {response.status_code}")
        return None

def display_metrics(run_id):
    summary = fetch_test_run_summary(run_id)
    if not summary:
        return
    with cols[1]:
        st.metric("Total Tests", f"{summary['total']}")
    with cols[3]:
        st.metric("Passed Tests", f"{summary['passed']}")
    with cols[5]:
        st.metric("Failed Tests", f"{summary['failed']}")
    with cols[7]:
        st.metric("Aborted Tests", f"{summary['aborted']}")


def analyze_and_plot(run_id):
    data = fetch_run_results(run_id)
    
    if not data:
        return
    
    classification_counts = {key: 0 for key in class_keywords.keys()}
    classification_counts["Unclassified"] = 0
    keyword_counts = {key: {kw: 0 for kw in keywords} for key, keywords in class_keywords.items()}

    for result in data.get('value', []):
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
            "subtext": f"Run ID: {run_id}",
            "left": "center",
            "textStyle": {"color": "#FFFFFF", "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {d}%"
        },
         
        "legend": {
             "orient": "vertical",
             "left": "left",
             "textStyle": {
                    "color": "#FFFFFF",
                    "fontSize": 12     
                },
             "backgroundColor": "rgba(50, 50, 50, 0.7)", 
             "borderRadius": 5, 
             "padding": [10, 15, 10, 15] 
        },
        "series": [
            {
                "name": "Error Classification",
                "type": "pie",
                "radius": "60%",
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
        # Define the columns within the container
        col1, col2, col3 = st.columns([1, 2, 4])
        # Merge the middle columns for the pie chart
        with col1:
            pass  # This could also be an empty placeholder or pass
        with col2:
            pass  # Empty column to be merged with the pie chart
        with col3:
            st_echarts(option_pie, height="500px")  # This is where the pie chart is placed

    

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

    if unclassified_errors:
     st.subheader("Unclassified Errors:")
     for error in unclassified_errors:
      st.text(error)


with cols[0]:
    run_id = st.text_input("Enter the run ID:")
if st.button("Analyze"):
    display_metrics(run_id)
    analyze_and_plot(run_id)

  