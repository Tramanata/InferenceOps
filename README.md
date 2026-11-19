# InferenceOps

A local learning project for deploying, measuring, and improving a machine learning inference service. The current checkpoint is a working CPU inference server and a Python client that displays object-detection results.

## What works today

- Roboflow Inference Server runs locally in a Docker container managed by Docker Compose.
- A Python client sends an image to the server using the Inference SDK.
- The server runs a pretrained RF-DETR object detector and returns predictions.
- Supervision draws bounding boxes and labels on the original image and displays it.
- Client dependencies are recorded with exact versions in `requirements.txt`.

A successful request and visualization have been verified manually. Latency, throughput, and memory benchmarks have not been recorded yet.

## How the pieces fit together

```text
Docker Compose -> starts Roboflow Inference Server in a CPU container

Python client -> downloads the public test image
              -> sends image + model ID to localhost:9001
              <- receives predictions from the server
              -> Supervision draws boxes and labels and displays the image
```

Inference means using a trained model to make predictions. The inference server is the application that accepts requests, loads the selected model, prepares inputs, runs the model, and returns results. The model determines object classes, confidence scores, and bounding-box coordinates; Supervision visualizes those predictions.

Model execution happens locally inside the container. The current workflow still needs internet access for the public image and for model-resource access when required. An API key does not mean inference is running in Roboflow's cloud.

## Repository files

| File | Purpose |
| --- | --- |
| `compose.yaml` | Defines the inference server's image, container settings, port mapping, cache, and privilege restrictions. |
| `client.py` | Loads configuration, retrieves the image, requests predictions, and visualizes the response. |
| `requirements.txt` | Records the Python packages installed for the client, including transitive dependencies. |
| `.gitignore` | Excludes the private `.env` file. The local `.venv/` directory should also be excluded before committing. |

## Server configuration

The service uses Roboflow's prebuilt CPU image. Compose uses that image to create a container; it does not build a custom inference server image from this repository.

- Port 9001 is published on `127.0.0.1`, allowing the client on this PC to reach the server.
- The host directory `${HOME}/.inference/cache` is mounted read-write at `/tmp`, preserving cached model resources across container replacement.
- The container root filesystem is read-only.
- Linux capabilities are dropped, with `NET_BIND_SERVICE` added back, and `no-new-privileges` is enabled.

The image currently uses the mutable `latest` tag. A fixed version or digest is needed before making reproducible benchmark comparisons. The file also retains an obsolete top-level `version` field, which modern Compose ignores with a warning.

## Client environment and model

The client uses a Python 3.12 virtual environment named `.venv`. This keeps its packages separate from Ubuntu's system Python. The SDK installation rejected the machine's Python 3.14 environment, so uv was used to create a compatible Python 3.12 environment.

The client uses:

- **Inference SDK** to communicate with the local server over HTTP.
- **python-dotenv** to load the project-root `.env` file.
- **Supervision** to retrieve the test image, convert predictions, and render annotations.

The selected model for this project is **RF-DETR Nano** (`rfdetr-nano`). Configure the client's model ID to use this alias for the baseline. No custom model training has been performed for this project.

## Recreating the current setup

1. Install Docker with the Compose plugin and install uv.
2. Create and activate a Python 3.12 virtual environment in `.venv`.
3. Install the dependencies listed in `requirements.txt` into that environment.
4. Create a private `.env` file beside `client.py`, containing a valid `ROBOFLOW_API_KEY`. The client reads this value and supplies it to the SDK using header transport. Do not commit the key.
5. Start the inference service using the repository's Compose configuration. If an older manually created container uses the same name or port, stop and remove that container first, preserving the cache directory.
6. Confirm the server page responds at [localhost:9001](http://localhost:9001).
7. Run `client.py` using the activated environment. The current client downloads the public walking-people image, requests predictions, and opens a visualization. Displaying the image requires a graphical session.

The `.env` file and `.venv` directory serve different purposes: one stores private configuration, while the other contains the client interpreter and installed packages. Neither belongs in Git.

## Next checkpoint: a repeatable baseline

- Confirm the client selects Nano and save a fixed test image locally.
- Pin the server image version or digest and record machine specifications and software versions.
- Measure client-observed request latency without image downloading or visualization in the timed section.
- Separate initial model loading from warmed-up requests, and record whether model files were already cached.
- Record repeated-request latency, request failures, and container memory before and after model loading.

Later project stages will add Kubernetes deployment, observability, load testing, scaling, and reliability experiments. These are planned work, not completed capabilities.

## References

- [Roboflow Inference Server installation on Linux](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/linux)
- [Run a model on a local inference server](https://docs.roboflow.com/deployment/self-hosted/self-hosted#run-model-locally)
- [Pretrained model aliases](https://docs.roboflow.com/models/pretrained-aliases)
- [Supervision documentation](https://supervision.roboflow.com/)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
- [Python virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
