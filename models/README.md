# Offline Model Files

Put pre-downloaded model files here. Docker Compose mounts this directory read-only at `/opt/airflow/models`.

Multiple models can coexist, each in its own subdirectory named after the HuggingFace ID (with `/` replaced by `-`):

```text
models/
  embedding/
    <model-dir>/
      config.json
      model.safetensors
      tokenizer.json
      tokenizer_config.json
      ...
    <another-model-dir>/
      ...
    <third-model-dir>/
      ...
```

## Runtime configuration

| Variable | Value | Purpose |
|---|---|---|
| `EMBEDDING_MODELS_DIR` | `/opt/airflow/models/embedding` | Parent directory containing all packaged embedding models |

The Airflow image only provides the Python runtime and offline environment. Docker Compose mounts `./models` read-only to `/opt/airflow/models`; the image does not contain model weights.

## Downloading models

Download model files on a machine with network access and copy the complete model directory into `./models/embedding/` before starting Airflow. Example:

```bash
python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="<org>/<model>",
    local_dir="models/embedding/<org>-<model>",
    local_dir_use_symlinks=False,
)
PY
```

## Important

- **Do not commit large model files to git.** Keep them on the deployment host, a mounted disk, or a shared filesystem.
- **Offline mode is enforced** in the Dockerfile (`TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`), so the model must be present in the mounted directory.
