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

| Variable | Value | Purpose |
|---|---|---|
| `EMBEDDING_MODELS_DIR` | `/opt/airflow/models/embedding` | Parent directory containing all packaged embedding models |

The Airflow image does not choose a specific model. Business code should choose the model through its own configuration and resolve it under `EMBEDDING_MODELS_DIR`.

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
