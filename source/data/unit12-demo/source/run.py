from pathlib import Path
import sys


input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
value = int(input_path.read_text(encoding="utf-8").strip())
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(f"{value}\n", encoding="utf-8", newline="\n")
