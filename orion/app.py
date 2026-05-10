from pathlib import Path
import importlib.util
import sys

from flask import request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("orion_root_app", ROOT / "app.py")
module = importlib.util.module_from_spec(spec)
sys.modules["orion_root_app"] = module
spec.loader.exec_module(module)

app = module.app

try:
    from math_service import answer_math

    original_ask_ai_response = module.ask_ai_response

    def ask_ai_response_with_math(message, context):
        reply = answer_math(message)
        if reply:
            return reply, "math"
        return original_ask_ai_response(message, context)

    module.ask_ai_response = ask_ai_response_with_math
except Exception:
    pass


@app.after_request
def orion_v111_patch(response):
    content_type = response.headers.get("Content-Type", "")
    if request.endpoint == "index" and "text/html" in content_type:
        html = response.get_data(as_text=True)
        html = html.replace("ORION V1.1", "ORION V1.1.1")
        html = html.replace("V1.1 Foundation", "V1.1.1 Foundation")
        html = html.replace("Interface V1.1 carregada", "Interface V1.1.1 carregada")
        html = html.replace("<title>ORION V1.1</title>", "<title>ORION V1.1.1</title>")
        style = """
<style id="orion-v111-logo-patch">
.logo {
  display: inline-block;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border: 1px solid rgba(0, 229, 255, 0.72);
  border-radius: 50%;
  background: url('/static/icon-192.png') center / cover no-repeat, rgba(13, 17, 23, 0.72);
  box-shadow: 0 0 18px rgba(0, 229, 255, 0.32);
}
.logo.large { width: 48px; height: 48px; }
</style>
"""
        if "orion-v111-logo-patch" not in html:
            html = html.replace("</head>", f"{style}</head>")
        response.set_data(html)
        response.headers["Content-Length"] = str(len(response.get_data()))
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
