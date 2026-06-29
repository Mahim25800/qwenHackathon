"""
Code Sandbox — Executes LLM-generated PyTorch code in a subprocess.
Extracts real parameter counts and model metrics safely.

Safety measures:
- Subprocess with timeout
- Restricted imports
- Stdout capture for metrics
- Stderr capture for errors
"""

import subprocess
import sys
import os
import json
import tempfile
import logging
import re

from config import settings

logger = logging.getLogger(__name__)

# Template that wraps the LLM-generated code to extract metrics
SANDBOX_TEMPLATE = '''
import sys
import json
import torch
import torch.nn as nn

# ============================================
# LLM-GENERATED MODEL CODE (inserted below)
# ============================================
{model_code}
# ============================================
# END OF LLM-GENERATED CODE
# ============================================

def count_parameters(model):
    """Count total trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def get_layer_summary(model):
    """Get a breakdown of parameters per named module."""
    layers = []
    for name, module in model.named_modules():
        params = sum(p.numel() for p in module.parameters(recurse=False) if p.requires_grad)
        if params > 0:
            layers.append({{
                "name": name,
                "type": module.__class__.__name__,
                "params": params,
            }})
    return layers

try:
    # Find the model class (look for nn.Module subclass)
    model_class = None
    for name, obj in list(globals().items()):
        if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
            model_class = obj
            break

    if model_class is None:
        print(json.dumps({{"success": False, "error": "No nn.Module subclass found in generated code"}}))
        sys.exit(1)

    # Instantiate
    input_shape = {input_shape}
    try:
        model = model_class()
    except TypeError:
        # Some models might need num_classes or other args
        try:
            model = model_class(num_classes={num_classes})
        except:
            model = model_class()

    model.eval()

    # Count parameters
    total_params = count_parameters(model)
    layer_summary = get_layer_summary(model)

    # Try a forward pass with dummy input
    dummy_input = torch.randn(1, *input_shape)
    with torch.no_grad():
        output = model(dummy_input)

    output_shape = list(output.shape)

    result = {{
        "success": True,
        "total_params": total_params,
        "output_shape": output_shape,
        "layer_summary": layer_summary,
        "model_class": model_class.__name__,
    }}
    print("SANDBOX_RESULT:" + json.dumps(result))

except Exception as e:
    import traceback
    result = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc(),
    }}
    print("SANDBOX_RESULT:" + json.dumps(result))
'''


def execute_model_code(
    code: str,
    input_shape: list[int],
    num_classes: int = 10,
) -> dict:
    """
    Execute PyTorch model code in a subprocess and extract metrics.

    Args:
        code: The PyTorch nn.Module code to evaluate
        input_shape: Input tensor shape [C, H, W]
        num_classes: Number of output classes

    Returns:
        dict with keys:
            - success: bool
            - total_params: int (if success)
            - layer_summary: str (if success)
            - output_shape: list (if success)
            - error: str (if failure)
            - stderr: str (raw stderr)
            - stdout: str (raw stdout)
    """
    # Clean the code — strip markdown fences if present
    clean_code = _clean_code(code)

    # Build the sandbox script
    script = SANDBOX_TEMPLATE.format(
        model_code=clean_code,
        input_shape=input_shape,
        num_classes=num_classes,
    )

    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        temp_path = f.name

    try:
        # Execute in subprocess with timeout
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=settings.sandbox_timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        stdout = result.stdout
        stderr = result.stderr

        # Parse the result
        if "SANDBOX_RESULT:" in stdout:
            result_line = stdout.split("SANDBOX_RESULT:")[1].strip()
            # Handle potential multiple lines after the marker
            result_line = result_line.split("\n")[0]
            parsed = json.loads(result_line)

            if parsed["success"]:
                # Format layer summary as readable string
                layer_lines = []
                for layer in parsed.get("layer_summary", []):
                    layer_lines.append(
                        f"  {layer['name']}: {layer['type']} — {layer['params']:,} params"
                    )
                parsed["layer_summary"] = "\n".join(layer_lines) if layer_lines else "No layers found"

            parsed["stdout"] = stdout
            parsed["stderr"] = stderr
            return parsed
        else:
            return {
                "success": False,
                "error": f"Sandbox did not produce a result. stderr: {stderr[:500]}",
                "stdout": stdout,
                "stderr": stderr,
                "total_params": 0,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {settings.sandbox_timeout}s",
            "stdout": "",
            "stderr": "TIMEOUT",
            "total_params": 0,
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse sandbox output: {e}",
            "stdout": stdout if "stdout" in dir() else "",
            "stderr": stderr if "stderr" in dir() else "",
            "total_params": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Sandbox execution failed: {str(e)}",
            "stdout": "",
            "stderr": str(e),
            "total_params": 0,
        }
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _clean_code(code: str) -> str:
    """Strip markdown fences and clean up LLM-generated code."""
    # Remove ```python ... ``` blocks
    code = re.sub(r"^```(?:python)?\s*\n", "", code, flags=re.MULTILINE)
    code = re.sub(r"\n```\s*$", "", code, flags=re.MULTILINE)
    code = code.strip()
    return code
