"""
Execution result normalization layer.

Converts raw task-runner output into a stable, structured contract
used by the rest of the orchestrator.
"""

from typing import Any


def normalize_execution_result(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize raw execution result into stable contract.

    Returns:
        {
            "success": bool,
            "status": str,        # "success" or "failure"
            "output": str,        # combined human-readable output
            "failure_text": str,  # extracted failure reason or ""
            "changed_files": list,
            "deliverables_updated": list,
            "raw_stdout": str,
            "raw_stderr": str,
            "returncode": int,
        }
    """
    # Handle missing keys gracefully
    returncode = raw.get("returncode", 0)
    success = raw.get("success", returncode == 0)
    
    raw_stdout = raw.get("stdout", "")
    raw_stderr = raw.get("stderr", "")
    
    # Build combined output
    output_parts = []
    if raw_stdout:
        output_parts.append(raw_stdout)
    if raw_stderr:
        output_parts.append(raw_stderr)
    output = "\n".join(output_parts).strip()
    
    # Extract failure text
    failure_text = ""
    if not success:
        # Use explicit failure_text if provided
        failure_text = raw.get("failure_text", "")
        
        # Otherwise try stderr first, then stdout
        if not failure_text:
            failure_text = raw_stderr.strip() or raw_stdout.strip()
        
        # Detect missing deliverables pattern
        if not failure_text and "missing" in output.lower() and "deliverable" in output.lower():
            failure_text = "Missing required deliverables"
    
    # Extract changed files from stdout if present
    changed_files = raw.get("changed_files", [])
    if not changed_files and raw_stdout:
        # Attempt to parse changed files from stdout
        # This is a simple heuristic for future task runner output
        for line in raw_stdout.split("\n"):
            if line.strip().startswith("CHANGED:"):
                changed_files.append(line.replace("CHANGED:", "").strip())
    
    deliverables_updated = raw.get("deliverables_updated", [])
    
    status = "success" if success else "failure"
    
    return {
        "success": success,
        "status": status,
        "output": output or "No output",
        "failure_text": failure_text,
        "changed_files": changed_files,
        "deliverables_updated": deliverables_updated,
        "raw_stdout": raw_stdout,
        "raw_stderr": raw_stderr,
        "returncode": returncode,
    }
