from flask import Flask, render_template
from sdwan import SDWANController, NetworkLink, TrafficFlow
import os

app = Flask(__name__, template_folder='templates')

@app.route("/")
def dashboard():
    controller = SDWANController()
    # Setup your network (same as before)
    controller.add_node("HQ", "hub")
    controller.add_node("Branch1", "cpe")
    controller.add_node("Branch2", "cpe")
    controller.add_node("CloudGW", "cloud")
    
    controller.add_link("HQ", "Branch1", NetworkLink(30, 5, 0.1, 50, 1))
    controller.add_link("HQ", "Branch2", NetworkLink(40, 8, 0.2, 50, 1))
    controller.add_link("Branch1", "Branch2", NetworkLink(20, 3, 0.05, 20, 2))
    controller.add_link("Branch1", "CloudGW", NetworkLink(60, 15, 0.3, 100, 3))
    controller.add_link("Branch2", "CloudGW", NetworkLink(70, 20, 0.4, 100, 3))
    
    controller.add_traffic_flow("voip1", TrafficFlow("Branch1", "HQ", 0.5, 1, "latency"))
    controller.add_traffic_flow("backup1", TrafficFlow("Branch1", "CloudGW", 20, 4, "throughput"))
    controller.add_traffic_flow("video1", TrafficFlow("Branch2", "HQ", 5, 2, "reliability"))
    
    results = controller.simulate_traffic()
    return render_template("dashboard.html", results=results)

if __name__ == "__main__":
    app.run(debug=True, port=5000)