import supervision as sv
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ROBOFLOW_API_KEY")

image = sv.load_image_from_url("https://media.roboflow.com/inference/people-walking.jpg")

client = InferenceHTTPClient(
    api_url="http://localhost:9001",
    api_key=api_key,
).configure(InferenceConfiguration(api_key_transport="header"))
results = client.infer(image, model_id="rfdetr-nano")

detections = sv.Detections.from_inference(results)

annotated_image = sv.BoxAnnotator().annotate(scene=image, detections=detections)
annotated_image = sv.LabelAnnotator().annotate(scene=annotated_image, detections=detections)

sv.plot_image(annotated_image)