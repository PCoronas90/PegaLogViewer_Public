from flask import Flask, render_template, request, flash, redirect
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)
app.secret_key = "supersecretkey"  

PASTEL_CLASSES = [
    'table-primary', 'table-secondary', 'table-success',
    'table-warning', 'table-info', 'table-light', ''
]
FAIL_CLASS = 'table-danger'

def assign_class(activity_name, class_map):
    if not activity_name:
        return "default"
    if activity_name not in class_map:
        class_map[activity_name] = PASTEL_CLASSES[len(class_map) % len(PASTEL_CLASSES)]
    return class_map[activity_name]

@app.route("/", methods=["GET", "POST"])
def index():
    events = []
    filters = {k: set() for k in [
        "DateTime", "ActivityName", "PrimaryPageName", "PrimaryPageClass",
        "StepMethod", "StepStatus", "EventType", "EventName", "RuleSet"
    ]}
    class_map = {}

    if request.method == "POST":
        file = request.files.get("logfile")
        if not file:
            flash("Nessun file caricato!", "danger")
            return redirect(request.url)

        if not file.filename.endswith(".xml"):
            flash("File non valido! Carica un file XML.", "danger")
            return redirect(request.url)

        try:
            tree = ET.parse(file)
            root = tree.getroot()
        except ET.ParseError:
            flash("Errore nel parsing del file XML: file corrotto o non valido.", "danger")
            return redirect(request.url)

        for trace_event in root.findall("TraceEvent"):
            activity_name = trace_event.findtext("ActivityName", "").strip()
            step_status = trace_event.findtext("mStepStatus", "") or trace_event.get("stepStatus", "")
            step_status = step_status.lower() if step_status else ""
            raw_xml = ET.tostring(trace_event, encoding="unicode")
            pretty_xml = minidom.parseString(raw_xml).toprettyxml(indent="  ")


            bgclass = FAIL_CLASS if "fail" in step_status or "exception" in step_status else assign_class(activity_name, class_map)

            event = {
                "DateTime": trace_event.findtext("DateTime", ""),
                "ActivityName": activity_name,
                "PrimaryPageName": trace_event.findtext("PrimaryPageName", ""),
                "PrimaryPageClass": trace_event.findtext("PrimaryPageClass", ""),
                "StepMethod": trace_event.findtext("StepMethod", "") or trace_event.get("stepMethod", ""),
                "StepStatus": step_status,
                "EventType": trace_event.findtext("EventType", "") or trace_event.get("eventType", ""),
                "EventName": trace_event.findtext("EventName", ""),
                "RuleSet": trace_event.get("rsname", ""),
                "raw": pretty_xml,
                "bgclass": bgclass
            }

            for key in filters:
                filters[key].add(event[key])
            events.append(event)

    filters = {k: sorted(v) for k, v in filters.items()}
    return render_template("index.html", events=events, filters=filters)

if __name__ == "__main__":
    app.run(debug=True)
