"""Execute a trusted project notebook without opening a kernel socket."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import sys
import argparse
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument("notebook", nargs="?", default="notebooks/03-graph-comparison.ipynb")
args = parser.parse_args()
path = (ROOT / args.notebook).resolve()
notebook = nbformat.read(path, as_version=4)
shell = InteractiveShell.instance()
count = 0
for cell in notebook.cells:
    if cell.cell_type != "code":
        continue
    count += 1
    print(f"Executing cell {count}", flush=True)
    with capture_output(stdout=True, stderr=True, display=True) as captured:
        result = shell.run_cell(cell.source, store_history=True)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError(captured.stdout + captured.stderr) from (result.error_before_exec or result.error_in_exec)
    outputs = []
    if captured.stdout:
        outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
    if captured.stderr:
        outputs.append(nbformat.v4.new_output("stream", name="stderr", text=captured.stderr))
    for rich in captured.outputs:
        outputs.append(nbformat.v4.new_output("display_data", data=rich.data, metadata=rich.metadata))
    cell.outputs = outputs
    cell.execution_count = count
notebook.metadata.language_info.version = sys.version.split()[0]
nbformat.validate(notebook)
nbformat.write(notebook, path)
record = {
    "notebook": str(path.relative_to(ROOT)),
    "code_cells_executed": count,
    "error_outputs": 0,
    "status": "passed",
    "executed_utc": datetime.now(timezone.utc).isoformat(),
    "execution_mode": "Sequential IPython execution in one process, with captured rich outputs",
    "environment_note": "Kernel sockets are unavailable in this build environment. Cell logic and rich outputs were executed in process; VS Code kernel connectivity remains a local setup check.",
}
milestone = notebook.metadata.get("milestone", 1)
(ROOT / f"validation/milestone-{milestone}-notebook-execution.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
