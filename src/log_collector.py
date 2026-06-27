import subprocess


def get_pod_logs(pod_name, namespace="default", tail=50):
    try:
        cmd = [
            "kubectl",
            "logs",
            pod_name,
            "-n",
            namespace,
            "--tail",
            str(tail),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error fetching logs: {result.stderr}"

        return result.stdout.strip()

    except Exception as e:
        return f"Exception: {str(e)}"
    

def get_pod_by_app(app_label, namespace="default"):
    try:
        cmd = [
            "kubectl",
            "get",
            "pods",
            "-n",
            namespace,
            "-l",
            f"app={app_label}",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return None

        return result.stdout.strip()

    except Exception:
        return None
