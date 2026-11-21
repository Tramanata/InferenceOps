import supervision as sv
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from dotenv import load_dotenv
import os
import time
import statistics
from PIL import Image



load_dotenv()

api_key = os.getenv("ROBOFLOW_API_KEY")

image = Image.open("people-walking.jpg")
image.load()

client = InferenceHTTPClient(
    api_url="http://localhost:9001",
    api_key=api_key,
).configure(InferenceConfiguration(api_key_transport="header"))

list_latencies = []
for i in range(20):
    start = time.perf_counter()
    results = client.infer(image, model_id="rfdetr-nano")
    end = time.perf_counter()
    request_latency = (end - start) * 1000  # Convert to milliseconds
    list_latencies.append(request_latency)
    print(f"Request latency: {request_latency:.2f} ms")


print(f"Average latency: {statistics.mean(list_latencies):.2f} ms")
print(f"Median latency: {statistics.median(list_latencies):.2f} ms")
print(f"Minimum latency: {min(list_latencies):.2f} ms")
print(f"Maximum latency: {max(list_latencies):.2f} ms")

detections = sv.Detections.from_inference(results)

annotated_image = sv.BoxAnnotator().annotate(scene=image, detections=detections)
annotated_image = sv.LabelAnnotator().annotate(scene=annotated_image, detections=detections)

sv.plot_image(annotated_image)