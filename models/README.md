# Offline Model Files

Put pre-downloaded model files here before building the Airflow image.

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

Pick a model by setting two related env vars (typically in Apollo):

| Variable | Value | Purpose |
|---|---|---|
| `EMBEDDING_MODELS_DIR` | `/opt/airflow/models/embedding` | Parent directory containing all packaged embedding models |
| `EMBEDDING_MODEL_NAME` | `<subdir>` | Selected model directory name under `EMBEDDING_MODELS_DIR` |
| `EMBEDDING_MODEL_PATH` | `/opt/airflow/models/embedding/<subdir>` | Optional explicit selected model path |
| `SMS_TEMPLATE_SCENE_EMBEDDING_MODEL` | `<HF ID>` | Identifier written into `dim_sms_template_scene_dict.embedding_model` |

The Dockerfile does not choose a specific model. Set `EMBEDDING_MODEL_NAME` or `EMBEDDING_MODEL_PATH` per deployment or through Apollo.

## Downloading models

Use the project script with the model you want to package:

```bash
# in the project root
bash scripts/download_embedding_model.sh <org>/<model>
```

The script downloads to `<project>/models/embedding/<org>-<name>/`. Copy that subdirectory into the Airflow `models/embedding/` build context before `docker compose build`.

## Important

- **Do not commit large model files to git.** They go through your image build pipeline.
- **Offline mode is enforced** in the Dockerfile (`TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`), so the model must be present locally in the image.
- **Online Java service** loading the same model must use a path / cache that resolves to the same HF ID written into `dim_sms_template_scene_dict.embedding_model`.
