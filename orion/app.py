from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("orion_root_app", ROOT / "app.py")
module = importlib.util.module_from_spec(spec)
sys.modules["orion_root_app"] = module
spec.loader.exec_module(module)

app = module.app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
