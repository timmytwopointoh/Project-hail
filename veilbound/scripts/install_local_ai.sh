#!/usr/bin/env bash
# Self-hosted CPU-only Ollama inference on each ephemeral GitHub Actions worker.
# No token, remote AI API, hosted model service, open listener or game upload.
set -euo pipefail

MODEL="${VEILBOUND_LOCAL_MODEL:-qwen2.5-coder:1.5b}"
if [[ ! "$MODEL" =~ ^qwen2[.]5-coder:(0[.]5b|1[.]5b|3b)$ ]]; then
  echo "Only reviewed, bounded self-hosted Qwen Coder models are allowed" >&2
  exit 2
fi
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=2m

if ! command -v ollama >/dev/null 2>&1; then
  # Official Ollama installer. Only run on trusted CI branch code and
  # with no GitHub checkout credentials or cloud-model API secrets.
  curl -fsSL --retry 3 https://ollama.com/install.sh -o /tmp/veilbound-ollama-install.sh
  sh /tmp/veilbound-ollama-install.sh
fi

if ! curl -fsS --max-time 2 http://127.0.0.1:11434/api/version >/dev/null; then
  nohup env OLLAMA_HOST="$OLLAMA_HOST" OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_KEEP_ALIVE=2m \
    ollama serve >/tmp/veilbound-local-ai.log 2>&1 &
fi
for attempt in $(seq 1 45); do
  if curl -fsS --max-time 2 http://127.0.0.1:11434/api/version >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS --max-time 2 http://127.0.0.1:11434/api/version >/dev/null || {
  echo "Local inference engine did not start" >&2
  exit 1
}
echo "Downloading the reviewed open-weight model to this ephemeral runner: $MODEL"
ollama pull "$MODEL"
echo "Local VEILBOUND model ready on loopback only."
