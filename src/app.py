import argparse
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from log_collector import get_pod_logs
from log_collector import get_pod_by_app

import ollama


APP_DIR = Path(__file__).resolve().parent
PROMPT_FILE = APP_DIR / "prompts" / "incident_analysis.txt"
REPORTS_DIR = APP_DIR / "reports"
DEFAULT_MODEL = "mistral"

DEMO_INCIDENTS = [
    "Payment API returning 500 errors after latest deployment",
    "Kubernetes pods in CrashLoopBackOff for order-service",
    "Redis connection timeout causing checkout failures",
    "High CPU usage on api-gateway with p99 latency spike",
    "Database connection pool exhausted during traffic peak",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI DevOps Assistant for incident analysis with local Ollama models"
    )
    parser.add_argument("incident", nargs="?", help="Production incident text")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for incident text in interactive mode",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with a random prebuilt demo incident",
    )
    parser.add_argument(
        "--list-demos",
        action="store_true",
        help="Show available demo incidents and exit",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Model temperature (default: 0.2)",
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=600,
        help="Maximum output tokens to predict (default: 600)",
    )
    parser.add_argument(
        "--stream",
        dest="stream",
        action="store_true",
        help="Stream output token-by-token",
    )
    parser.add_argument(
        "--no-stream",
        dest="stream",
        action="store_false",
        help="Return full output after completion",
    )
    parser.set_defaults(stream=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated prompt and exit without calling Ollama",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save generated analysis to reports/*.md",
    )
    parser.add_argument(
    "--pod",
    help="Fetch logs from Kubernetes pod"
    )

    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace (default: default)"
    )

    parser.add_argument(
        "--tail",
        type=int,
        default=50,
        help="Number of log lines (default: 50)"
    )

    
    parser.add_argument(
        "--app",
        help="Kubernetes app label (auto-detect pod)"
    )

    return parser.parse_args()


def load_prompt_template() -> str:
    with PROMPT_FILE.open("r", encoding="utf-8") as file:
        return file.read()


def build_prompt(incident: str) -> str:
    return load_prompt_template().replace("{incident}", incident.strip())


def print_banner() -> None:
    print("=" * 72)
    print("  AI SRE Engineer  |  Python + Ollama (Local LLM) + Kubernetes")
    print("=" * 72)


def show_demo_incidents() -> None:
    print("\nAvailable demo incidents:")
    for idx, item in enumerate(DEMO_INCIDENTS, start=1):
        print(f"  {idx}. {item}")


def resolve_incident(args: argparse.Namespace) -> str:
    if args.app:
        print(f"\nFinding pod for app: {args.app}")

        pod_name = get_pod_by_app(args.app, args.namespace)

        if not pod_name:
            raise ValueError("No pod found for given app label")

        print(f"Found pod: {pod_name}")

        logs = get_pod_logs(pod_name, args.namespace, args.tail)

        return f"Kubernetes Logs:\n{logs}"

    if args.pod:
        print(f"\nFetching logs from pod: {args.pod} (ns: {args.namespace})")
        logs = get_pod_logs(args.pod, args.namespace, args.tail)

        if not logs:
            raise ValueError("No logs found for the given pod.")

        print("\nCollected Logs (preview):")
        print("-" * 60)
        print(logs[:500])  # preview first 500 chars
        print("-" * 60)

        return f"Kubernetes Logs:\n{logs}"

    # Existing logic (unchanged)
    if args.demo:
        chosen = random.choice(DEMO_INCIDENTS)
        print(f"\nDemo incident selected: {chosen}")
        return chosen

    if args.interactive or not args.incident:
        entered = input("\nEnter production issue:\n> ").strip()
        if not entered:
            raise ValueError("Incident cannot be empty.")
        return entered

    return args.incident.strip()


def check_ollama_connection(model: str) -> None:
    try:
        available = ollama.list()
        models = {
            item.get("model")
            for item in available.get("models", [])
            if isinstance(item, dict)
        }
        if models and model not in models:
            print(
                f"\nWarning: model '{model}' is not available locally. "
                f"Run: ollama pull {model}"
            )
    except Exception as exc:
        print("\nCannot connect to Ollama.")
        print("Ensure Ollama is running on localhost before retrying.")
        print(f"Details: {exc}")
        raise SystemExit(1)


def generate_analysis(
    prompt: str,
    model: str,
    stream: bool,
    temperature: float,
    num_predict: int,
) -> str:
    print("\nRunning with local AI (Ollama)")
    print(f"Model    : {model}")
    print("Endpoint : http://localhost:11434")
    print(f"Stream   : {'ON' if stream else 'OFF'}")
    print("\nSending incident to local LLM...")

    options = {
        "temperature": temperature,
        "num_predict": num_predict,
    }

    if stream:
        print("Tokens will appear live below:\n")
        print("-" * 72)
        chunks = []
        response_stream = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options=options,
            stream=True,
        )
        for part in response_stream:
            token = part.get("message", {}).get("content", "")
            if token:
                print(token, end="", flush=True)
                chunks.append(token)
        print("\n" + "-" * 72)
        return "".join(chunks).strip()

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options=options,
        stream=False,
    )
    return response.get("message", {}).get("content", "").strip()


def save_report(incident: str, model: str, report: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", incident.lower()).strip("-")[:60]
    file_path = REPORTS_DIR / f"{timestamp}-{slug or 'incident-report'}.md"
    content = (
        f"# Incident Analysis Report\n\n"
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- Model: {model}\n"
        f"- Incident: {incident}\n\n"
        f"---\n\n"
        f"{report}\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def main() -> int:
    args = parse_args()
    print_banner()

    if args.list_demos:
        show_demo_incidents()
        return 0

    try:
        incident = resolve_incident(args)
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1

    print(f"\nIncident : {incident}")

    prompt = build_prompt(incident)
    if args.dry_run:
        print("\nDry-run mode: generated prompt preview\n")
        print("-" * 72)
        print(prompt)
        print("-" * 72)
        return 0

    check_ollama_connection(args.model)

    try:
        report = generate_analysis(
            prompt=prompt,
            model=args.model,
            stream=args.stream,
            temperature=args.temperature,
            num_predict=args.num_predict,
        )
    except Exception as exc:
        print(f"\nAnalysis failed: {exc}")
        return 1

    if not args.stream:
        print("\n" + "-" * 72)
        print(report)
        print("-" * 72)

    if args.save:
        saved = save_report(incident=incident, model=args.model, report=report)
        print(f"\nReport saved to: {saved}")

    print("\nDone. Review recommendations before production changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())