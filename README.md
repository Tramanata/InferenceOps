# InferenceOps

A local learning project for deploying, measuring, and improving a CPU machine learning inference service. Roboflow provides the inference server and pretrained model; this repository contains the deployment configuration, client, and measurement workflow.

## Current progress

- **Compose:** the inference server runs locally and has returned predictions successfully.
- **Client:** Python 3.12, the Inference SDK, and RF-DETR Nano process a fixed local image. Supervision displays bounding boxes and labels.
- **Timing:** the client measures 20 sequential requests and reports average, median, minimum, and maximum latency.
- **Kubernetes:** a single-node kind cluster runs the inference-server Deployment. The Pod started without restarts, and its web page was reached through port forwarding.
- **Still to verify:** an actual prediction through Kubernetes. The client currently targets the Compose server on port 9001.

## Architecture

```text
Python client in .venv
  -> loads people-walking.jpg and its pixels before timing
  -> sends image + rfdetr-nano model ID through the Inference SDK
  -> receives object classes, confidence scores, and box coordinates
  -> Supervision annotates the final response and displays the image

Server targets:
  Compose:     localhost:9001 -> inference-server container
  Kubernetes:  localhost:9002 -> kubectl port-forward -> Pod port 9001

Local Kubernetes environment:
  Linux PC -> Docker -> kind node container -> containerd -> inference Pod
```

Inference means using a trained model to make predictions. The server accepts requests, loads the selected model, prepares inputs, runs inference, and returns predictions. Supervision renders the results; it does not perform the detection.

Model execution happens locally inside the server container. Model resources may still require network access and Roboflow authentication. The client reads `ROBOFLOW_API_KEY` from a private project-root `.env` file and sends it using header transport. No custom model training has been performed.

## Repository

| File | Purpose |
| --- | --- |
| `compose.yaml` | Local CPU inference service, port mapping, persistent cache, and security settings. |
| `k8s/deployment.yaml` | One inference-server replica with matching labels and an `emptyDir` cache mounted at `/tmp`. |
| `client.py` | Loads the local image, makes 20 timed Nano requests, prints statistics, and visualizes the final response. |
| `people-walking.jpg` | Fixed local test image. |
| `requirements.txt` | Exact installed client package versions, including transitive dependencies. |
| `.env` | Local API key configuration; excluded from Git. |
| `.venv/` | Local Python 3.12 environment; should be excluded from Git. |

## Setup and operation

### Client environment

Install Docker with the Compose plugin and [uv](https://docs.astral.sh/uv/getting-started/installation/). From the repository root:

1. Create `.venv` using Python 3.12 and activate it. Python 3.14 was rejected by the SDK during setup; uv supplies a separate compatible interpreter.
2. Install the packages in `requirements.txt` into that environment.
3. Create `.env` beside `client.py` with a valid `ROBOFLOW_API_KEY`. Never commit the real key.
4. Keep `people-walking.jpg` in the repository root. Run the client from that directory because its image path is relative to the working directory.

The Python environment runs the client; Docker supplies the separate server environment. Displaying the annotated image requires a graphical session.

### Compose server

Start the service with Docker Compose using `compose.yaml`, then verify the page at [localhost:9001](http://localhost:9001). A manually created container with the same name or port must be stopped and removed before Compose can create its replacement.

The Compose configuration:

- Publishes port 9001 on `127.0.0.1` for local access.
- Mounts `${HOME}/.inference/cache` read-write at `/tmp`, preserving cache files across container replacement.
- Uses a read-only root filesystem, prevents privilege escalation through `no-new-privileges`, drops Linux capabilities, and adds back `NET_BIND_SERVICE`.

The file still includes an obsolete top-level `version` field. Modern Compose ignores it with a warning; it can be removed.

### Kubernetes server

Install [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) and [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/). The completed deployment sequence was:

1. Create the cluster with `kind create cluster --name inferenceops --wait 120s`.
2. Confirm the node is Ready using `kubectl --context kind-inferenceops get nodes`.
3. Validate the manifest using `kubectl --context kind-inferenceops apply --dry-run=server -f k8s/deployment.yaml`.
4. Apply it using `kubectl --context kind-inferenceops apply -f k8s/deployment.yaml`.
5. Inspect Pods, events, and application logs to check startup.
6. Run `kubectl --context kind-inferenceops port-forward deployment/inference-server 9002:9001` and leave that terminal open.
7. Open [localhost:9002](http://localhost:9002) to check HTTP access.

To test predictions through Kubernetes, change the client's API URL from port 9001 to port 9002 before running it. Otherwise, the current client continues to test Compose.

The Deployment runs one replica and mounts `emptyDir` at `/tmp`. This cache survives a container restart within the same Pod but is lost when the Pod is replaced. It is separate from the Compose cache. The Kubernetes manifest currently has no Service, readiness/startup probes, resource requests or limits, or Compose-equivalent security settings. Without a readiness probe, Pod readiness alone does not verify HTTP or model readiness.

## Initial latency results

The first reported 20-request local run produced:

| Metric | Client-observed latency |
| --- | ---: |
| Average | 150.92 ms |
| Median | 138.71 ms |
| Minimum | 126.26 ms |
| Maximum | 212.77 ms |

The client uses `time.perf_counter()` around each SDK inference call and converts seconds to milliseconds. Image loading and decoding happen before the loop; visualization happens afterward. These timings include SDK processing, HTTP communication, and server work, rather than model computation alone.

These are preliminary observations. The client has no explicit warm-up phase, and the model's loaded state at the start of the reported run was not recorded. Machine specifications and the exact server image used for that run were also not recorded. Memory and CPU were inspected with Docker stats, but numerical resource results were not captured. No throughput, concurrency, or Kubernetes latency comparison has been completed.

Both deployment configurations currently use the mutable `latest` image tag. Pin the same image version or digest in each before drawing benchmark comparisons.

## What I learned

- **Containers and images:** Roboflow's image packages the application; Compose records how to run it as a container.
- **Python environments:** `.venv` isolates the client interpreter and packages, while `.env` stores private configuration. Loading `.env` does not automatically define Python variables.
- **Request timing:** load and decode the test image before measuring; exclude visualization and distinguish initial loading from warmed-up requests.
- **Local Kubernetes:** kind creates a Docker container that acts as a Kubernetes node. Creating the cluster and deploying an application into it are separate steps.
- **Deployment configuration:** labels and selectors connect a Deployment to its Pods, while volume definitions and mounts belong at different YAML levels.
- **Cluster operations:** kubectl contexts select connection settings. Dry runs validate configuration; Pod descriptions and events explain startup; logs show application behavior; port forwarding provides local access.
- **Startup diagnosis:** the first Kubernetes image pull took about 96 seconds for a roughly 2.49 GB image. The waiting period was an image download, rather than an application failure.

## Next steps

1. **Verify Kubernetes predictions:** target port 9002 and confirm Nano returns predictions through the forwarded connection.
2. **Make comparison conditions repeatable:** pin the same server image, record CPU/RAM and software versions, add explicit warm-up requests, and save individual durations. Keep initial loading measurements separate and record cache state. Stop the unused inference instance during each comparison to reduce resource competition.
3. **Complete the Kubernetes configuration:** add a Service, startup/readiness probes, measured resource requests and limits, and suitable security settings. Decide whether cache persistence beyond a Pod's lifetime is needed.
4. **Measure and observe:** record memory and CPU, then introduce Prometheus and Grafana before load testing, SLOs, and scaling experiments. Treat port forwarding as development access; document a consistent access path for performance tests.
5. **Finish project hygiene:** add `.venv/` to `.gitignore` (currently only `.env` is listed) and remove the obsolete Compose `version` field.

Reliability experiments, CI checks, hardening, cost analysis, and the final write-up remain later milestones. This is a local learning study, not a production deployment.

## References

- [Roboflow Inference Server on Linux](https://docs.roboflow.com/deployment/self-hosted/inference-server/install/linux)
- [Local inference and model selection](https://docs.roboflow.com/deployment/self-hosted/self-hosted#run-model-locally)
- [Pretrained model aliases](https://docs.roboflow.com/models/pretrained-aliases)
- [Supervision](https://supervision.roboflow.com/)
- [Python performance counter](https://docs.python.org/3.12/library/time.html#time.perf_counter)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes emptyDir volumes](https://kubernetes.io/docs/concepts/storage/volumes/#emptydir)
