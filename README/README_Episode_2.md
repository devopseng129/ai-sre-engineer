# AI DevOps Assistant — Episode 02 (Local LLM with Ollama)

YouTube series: **AI SRE Engineer**  
Episode focus: Build a CLI AI assistant that analyzes production incidents using a **local** model.

This project is designed for content creators and learners who want practical AI + SRE demos without cloud APIs.

---

## What this project does

Given a production incident like:

```bash
python app.py "Payment API returning 500 errors"
```

the assistant generates a structured SRE response with:

- Incident summary
- Likely root causes
- Practical troubleshooting commands
- Recommended actions and prevention guidance

It runs on **Ollama** locally, so no API key is required.

---

## Project structure

```text
episode-02-ai-devops-assistant/
├── app.py
├── requirements.txt
├── README.md
├── .env
└── prompts/
    └── incident_analysis.txt
```

---

## Prerequisites

- Python 3.10+
- Ollama installed and running
- A local model pulled (default model used by app: `mistral`)

Install model:

```bash
ollama pull mistral
```

You can also use other models:

```bash
ollama pull llama3
ollama pull qwen2.5
```

---

## Setup

```bash
cd episode-02-ai-devops-assistant
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run options

### 1) Quick incident analysis (default streaming)

```bash
python app.py "Payment API returning 500 errors"
```

### 2) Interactive mode

```bash
python app.py --interactive
```

### 3) Use a different model

```bash
python app.py "Redis timeout in checkout" --model llama3
```

### 4) Disable streaming

```bash
python app.py "K8s CrashLoopBackOff" --no-stream
```

### 5) Preview prompt without calling Ollama

```bash
python app.py "Database errors" --dry-run
```

### 6) Save report to markdown

```bash
python app.py "High latency in api-gateway" --save
```

Saved files are written to:

```text
reports/*.md
```

---

## CLI flags reference

- `incident` (optional positional): Incident text
- `--interactive`: Ask incident through terminal input
- `--demo`: Pick a random built-in scenario
- `--list-demos`: Print demo scenarios and exit
- `--model`: Ollama model name (default: `mistral`)
- `--temperature`: Sampling temperature (default: `0.2`)
- `--num-predict`: Max generated tokens (default: `600`)
- `--stream`: Stream output token-by-token (default)
- `--no-stream`: Return full output at once
- `--dry-run`: Print generated prompt only
- `--save`: Save final report to `reports/`

---

---

## Troubleshooting

- **Cannot connect to Ollama**
  - Start Ollama app or run `ollama serve`
- **Model not found**
  - Pull model first, e.g. `ollama pull mistral`
- **Slow first response**
  - Normal behavior while model loads into memory
- **No useful output**
  - Try a clearer incident statement and increase detail

---

## Prompt customization

Edit the SRE behavior in:

```text
prompts/incident_analysis.txt
```

You can tune:

- Incident response structure
- Depth of root-cause analysis
- Preferred troubleshooting commands
- Organization-specific SRE style

---


Part of the **AI SRE Engineer** learning series.