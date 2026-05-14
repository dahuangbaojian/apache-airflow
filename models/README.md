# Offline Model Files

Put pre-downloaded model files here before building the Airflow image.

Recommended layout for embedding models:

```text
models/
  embedding/
    config.json
    model.safetensors
    tokenizer.json
    tokenizer_config.json
    ...
```

Runtime code should load the model from:

```bash
${EMBEDDING_MODEL_PATH:-/opt/airflow/models/embedding}
```

Do not commit large model files to git. Keep them in the build context locally or provide them through your image build pipeline.
