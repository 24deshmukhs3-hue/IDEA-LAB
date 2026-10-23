import json
import re

def analyze_telemetry_logs(log_content: str):
    """
    Parses application runtime logs to identify underutilized features
    based on relative invocation percentages and absolute thresholds.
    """
    invocation_counts = {}
    underutilized_features = []

    if not log_content.strip():
        return {
            "feature_analytics": [],
            "underutilized_summary": "No runtime logs provided for telemetry analysis."
        }

    # 1. Parse JSON or text logs
    try:
        logs = json.loads(log_content)
        if isinstance(logs, list):
            for entry in logs:
                func_name = entry.get("feature") or entry.get("function") or entry.get("endpoint")
                if func_name:
                    invocation_counts[func_name] = invocation_counts.get(func_name, 0) + 1
    except Exception:
        lines = log_content.splitlines()
        for line in lines:
            matches = re.findall(r'(?:CALLED|EXECUTE|ENDPOINT|FEATURE)[:\s]+([a-zA-Z0-9_]+)', line, re.IGNORECASE)
            for func_name in matches:
                invocation_counts[func_name] = invocation_counts.get(func_name, 0) + 1

    total_calls = sum(invocation_counts.values())

    # 2. Flag relative low utilization (e.g., < 15% of total system usage or < 3 calls)
    if total_calls > 0:
        for feature, count in invocation_counts.items():
            usage_percentage = (count / total_calls) * 100
            
            # Flag if feature represents < 15% of total execution volume OR < 3 calls
            if usage_percentage < 15.0 or count < 3:
                underutilized_features.append({
                    "feature": feature,
                    "invocation_count": count,
                    "percentage": round(usage_percentage, 1),
                    "status": "Low Relative Utilization",
                    "recommendation": f"Feature '{feature}' accounts for only {count} call(s) ({round(usage_percentage, 1)}% of total telemetry volume). Consider refactoring or evaluating for deprecation."
                })

    return {
        "feature_analytics": underutilized_features,
        "raw_counts": invocation_counts,
        "underutilized_summary": f"Identified {len(underutilized_features)} low-usage feature(s) from telemetry runtime analysis."
    }