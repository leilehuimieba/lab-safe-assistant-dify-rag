import json, os, sys, uvicorn
from pathlib import Path
cfg = json.loads(Path(__file__).with_name("launch_env.json").read_text(encoding="utf-8-sig"))
for key, value in cfg.items():
    if key == "WORKDIR":
        continue
    os.environ[key] = str(value or "")
os.chdir(cfg["WORKDIR"])
sys.path.insert(0, str(Path(cfg["WORKDIR"]).parent))
uvicorn.run("web_demo.app:app", host="127.0.0.1", port=int(cfg["DEMO_PORT"]))
