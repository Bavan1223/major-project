from flask import Flask, Response, jsonify, render_template_string
import json
import os

app = Flask(__name__)

LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logs",
    "events.jsonl"
)


HTML = """
<!DOCTYPE html>
<html>
<head>

    <title>Ransomware Defense SOC</title>

    <meta charset="UTF-8">

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: #05070a;
            color: #d1d5db;
            font-family: Arial, Helvetica, sans-serif;
        }

        .header {
            padding: 20px 30px;
            background: #090d12;
            border-bottom: 1px solid #1f2937;
        }

        .title {
            font-size: 26px;
            font-weight: bold;
            color: #e5e7eb;
        }

        .subtitle {
            margin-top: 7px;
            color: #6b7280;
            font-size: 13px;
        }

        .status {
            float: right;
            color: #22c55e;
            font-weight: bold;
        }

        .container {
            padding: 25px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }

        .card {
            background: #0b1117;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 20px;
        }

        .label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
        }

        .value {
            font-size: 30px;
            font-weight: bold;
            margin-top: 8px;
            color: #e5e7eb;
        }

        .risk {
            margin-top: 20px;
            padding: 22px;
            background: #0b1117;
            border: 1px solid #1f2937;
            border-radius: 8px;
        }

        .risk-normal {
            color: #22c55e;
        }

        .risk-high {
            color: #ef4444;
        }

        .risk-title {
            font-size: 22px;
            font-weight: bold;
        }

        .risk-description {
            margin-top: 8px;
            color: #9ca3af;
        }

        .section {
            margin-top: 20px;
            background: #0b1117;
            border: 1px solid #1f2937;
            border-radius: 8px;
            overflow: hidden;
        }

        .section-title {
            padding: 15px 20px;
            border-bottom: 1px solid #1f2937;
            font-size: 15px;
            font-weight: bold;
            color: #9ca3af;
            text-transform: uppercase;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 12px 15px;
            color: #6b7280;
            font-size: 11px;
            border-bottom: 1px solid #1f2937;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid #111827;
            font-size: 12px;
        }

        .red {
            color: #ef4444;
            font-weight: bold;
        }

        .green {
            color: #22c55e;
        }

        .blue {
            color: #60a5fa;
        }

        .yellow {
            color: #facc15;
        }

        .muted {
            color: #6b7280;
        }

        .mono {
            font-family: monospace;
        }

        .live-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 50%;
            margin-right: 6px;
        }

        @media(max-width: 900px) {

            .cards {
                grid-template-columns: repeat(2, 1fr);
            }

            .container {
                padding: 15px;
            }

            table {
                font-size: 11px;
            }
        }

    </style>

</head>


<body>

<div class="header">

    <span class="status">
        <span class="live-dot"></span>
        LIVE MONITORING
    </span>

    <div class="title">
        RANSOMWARE DEFENSE // SOC MONITOR
    </div>

    <div class="subtitle">
        Protected Host: Ubuntu Linux |
        IP: 192.168.74.131
    </div>

</div>


<div class="container">


    <!-- STATISTICS -->

    <div class="cards">

        <div class="card">

            <div class="label">
                File Events
            </div>

            <div class="value" id="file-count">
                0
            </div>

        </div>


        <div class="card">

            <div class="label">
                Network Events
            </div>

            <div class="value" id="network-count">
                0
            </div>

        </div>


        <div class="card">

            <div class="label">
                Detection Alerts
            </div>

            <div class="value" id="alert-count">
                0
            </div>

        </div>


        <div class="card">

            <div class="label">
                System Status
            </div>

            <div class="value green">
                ACTIVE
            </div>

        </div>

    </div>


    <!-- RISK -->

    <div class="risk">

        <div id="risk-title"
             class="risk-title risk-normal">

            🟢 SYSTEM NORMAL

        </div>

        <div id="risk-description"
             class="risk-description">

            No high-risk behavioral activity detected.

        </div>

    </div>


    <!-- NETWORK -->

    <div class="section">

        <div class="section-title">
            Network Activity
        </div>

        <table>

            <thead>

                <tr>

                    <th>TIME</th>
                    <th>SOURCE IP</th>
                    <th>DESTINATION</th>
                    <th>PID</th>
                    <th>PROCESS</th>
                    <th>STATUS</th>

                </tr>

            </thead>

            <tbody id="network-table">

            </tbody>

        </table>

    </div>


    <!-- LIVE EVENTS -->

    <div class="section">

        <div class="section-title">
            Live Event Stream
        </div>

        <table>

            <thead>

                <tr>

                    <th>TIME</th>
                    <th>SOURCE</th>
                    <th>EVENT</th>
                    <th>INDICATOR</th>
                    <th>PID</th>
                    <th>PROCESS</th>

                </tr>

            </thead>

            <tbody id="event-table">

            </tbody>

        </table>

    </div>


</div>


<script>


function loadEvents() {

    fetch("/api/events")

        .then(response => response.json())

        .then(data => {

            updateDashboard(data);

        })

        .catch(error => {

            console.log("Dashboard update error:", error);

        });

}


function updateDashboard(data) {


    /*
     * Statistics
     */

    document.getElementById(
        "file-count"
    ).innerText = data.file_events;


    document.getElementById(
        "network-count"
    ).innerText = data.network_events;


    document.getElementById(
        "alert-count"
    ).innerText = data.alerts;


    /*
     * Risk
     */

    const riskTitle =
        document.getElementById("risk-title");

    const riskDescription =
        document.getElementById("risk-description");


    if (data.risk === "HIGH") {

        riskTitle.className =
            "risk-title risk-high";

        riskTitle.innerText =
            "🔴 HIGH RISK DETECTED";

        riskDescription.innerText =
            data.reason;

    }

    else {

        riskTitle.className =
            "risk-title risk-normal";

        riskTitle.innerText =
            "🟢 SYSTEM NORMAL";

        riskDescription.innerText =
            "No high-risk behavioral activity detected.";

    }


    /*
     * Network table
     */

    const networkTable =
        document.getElementById("network-table");

    networkTable.innerHTML = "";


    data.network_events_list.forEach(event => {

        const row =
            document.createElement("tr");


        const d = event.data || {};


        let local =
            d.local_address || "-";

        let remote =
            d.remote_address || "-";


        let sourceIP = "-";

        let destination = remote;


        if (remote.includes(":")) {

            sourceIP =
                remote.substring(
                    0,
                    remote.lastIndexOf(":")
                );

        }


        row.innerHTML = `

            <td class="mono">
                ${event.timestamp || "-"}
            </td>

            <td class="blue mono">
                ${sourceIP}
            </td>

            <td class="mono">
                ${local}
            </td>

            <td>
                ${event.pid ?? "None"}
            </td>

            <td>
                ${event.process || "Unknown"}
            </td>

            <td class="green">
                ${d.status || "-"}
            </td>

        `;


        networkTable.appendChild(row);

    });


    /*
     * Live event table
     */

    const eventTable =
        document.getElementById("event-table");

    eventTable.innerHTML = "";


    data.recent_events.forEach(event => {

        const row =
            document.createElement("tr");


        let sourceClass = "muted";


        if (
            event.source ===
            "detection_engine"
        ) {

            sourceClass = "red";

        }

        else if (
            event.source ===
            "network_monitor"
        ) {

            sourceClass = "blue";

        }

        else if (
            event.source ===
            "file_monitor"
        ) {

            sourceClass = "yellow";

        }


        row.innerHTML = `

            <td class="mono">
                ${event.timestamp || "-"}
            </td>

            <td class="${sourceClass}">
                ${event.source || "-"}
            </td>

            <td>
                ${event.event_type || "-"}
            </td>

            <td>
                ${event.indicator || "-"}
            </td>

            <td>
                ${event.pid ?? "None"}
            </td>

            <td>
                ${event.process || "Unknown"}
            </td>

        `;


        eventTable.appendChild(row);

    });

}


/*
 * Initial load
 */

loadEvents();


/*
 * Update every second
 */

setInterval(
    loadEvents,
    1000
);


</script>


</body>

</html>
"""


def read_events():

    events = []

    if not os.path.exists(LOG_FILE):
        return events

    try:

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    event = json.loads(line)

                    events.append(event)

                except json.JSONDecodeError:

                    continue

    except OSError:

        pass

    return events


@app.route("/")
def dashboard():

    return render_template_string(HTML)


@app.route("/favicon.ico")
def favicon():

    return Response(status=204)


@app.route("/api/events")
def api_events():

    events = read_events()


    file_events = sum(
        1
        for event in events
        if event.get("source")
        == "file_monitor"
    )


    network_events = sum(
        1
        for event in events
        if event.get("source")
        == "network_monitor"
    )


    alerts = sum(
        1
        for event in events
        if event.get("source")
        == "detection_engine"
    )


    risk = (
        "HIGH"
        if alerts > 0
        else "NORMAL"
    )


    reason = (
        "Rapid mass file modification detected."
        if risk == "HIGH"
        else "No high-risk behavioral activity detected."
    )


    network_events_list = [
        event
        for event in events
        if event.get("source")
        == "network_monitor"
    ]

    network_events_list = (
        network_events_list[-10:]
    )

    network_events_list.reverse()


    recent_events = events[-20:]

    recent_events.reverse()


    return jsonify({

        "file_events":
            file_events,

        "network_events":
            network_events,

        "alerts":
            alerts,

        "risk":
            risk,

        "reason":
            reason,

        "network_events_list":
            network_events_list,

        "recent_events":
            recent_events

    })


if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )
    print(
        " RANSOMWARE DEFENSE // SOC MONITOR"
    )
    print(
        "=========================================="
    )
    print()
    print(
        "Dashboard:"
        " http://127.0.0.1:5000"
    )
    print()
    print("Live event source:")
    print(
        " logs/events.jsonl"
    )
    print()
    print("Press Ctrl+C to stop.")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
