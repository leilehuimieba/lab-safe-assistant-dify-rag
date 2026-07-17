from __future__ import annotations

import argparse
import re
import secrets
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.dify_rag"


def load_lines() -> list[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def upsert(lines: list[str], key: str, value: str) -> list[str]:
    rendered = f"{key}={value}"
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = rendered
            return lines
    lines.append(rendered)
    return lines


def value_for(lines: list[str], key: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def write_lines(lines: list[str]) -> None:
    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ensure_admin() -> None:
    lines = load_lines()
    defaults = {
        "DIFY_ADMIN_EMAIL": "lab-safe-admin@example.local",
        "DIFY_ADMIN_USERNAME": "LabSafetyAdmin",
        "DIFY_APP_NAME": "实验室安全小助手验收版",
    }
    for key, default in defaults.items():
        if not value_for(lines, key):
            lines = upsert(lines, key, default)
    if not value_for(lines, "DIFY_ADMIN_PASSWORD"):
        password = secrets.token_urlsafe(24)
        if not any(char.isdigit() for char in password):
            password += "7"
        lines = upsert(lines, "DIFY_ADMIN_PASSWORD", password)
    write_lines(lines)
    print("Local Dify administrator variables are present in the ignored env file.")


def rotate_admin_password() -> None:
    password = secrets.token_urlsafe(24)
    if not any(char.isdigit() for char in password):
        password += "7"
    lines = upsert(load_lines(), "DIFY_ADMIN_PASSWORD", password)
    write_lines(lines)
    print("The local Dify administrator password was rotated without displaying it.")


def set_from_stdin(key: str) -> None:
    allowed = {"DIFY_APP_API_KEY"}
    if key not in allowed:
        raise SystemExit(f"Refusing unsupported secret key: {key}")
    value = sys.stdin.read().strip()
    if key == "DIFY_APP_API_KEY" and not re.fullmatch(r"app-[A-Za-z0-9_-]{20,}", value):
        raise SystemExit("Input does not look like a Dify App API key.")
    lines = upsert(load_lines(), key, value)
    write_lines(lines)
    print(f"{key} was updated without displaying its value.")


def import_model_env(source: Path) -> None:
    if not source.is_file():
        raise SystemExit("Model source env file does not exist.")
    source_values: dict[str, str] = {}
    for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        source_values[key.strip()] = value.strip()
    api_key = source_values.get("OPENAI_API_KEY", "")
    api_base = source_values.get("OPENAI_BASE_URL", "")
    model = source_values.get("OPENAI_MODEL", "")
    if not api_key or len(api_key) < 20:
        raise SystemExit("Source model API key is missing or invalid.")
    if api_base.rstrip("/") != "https://api.deepseek.com":
        raise SystemExit("Only the validated official DeepSeek endpoint may be imported.")
    if not model.startswith("deepseek-"):
        raise SystemExit("Source model name is not a DeepSeek model.")
    lines = load_lines()
    for key, value in {
        "DIFY_MODEL_PROVIDER": "deepseek",
        "DIFY_MODEL_API_BASE": api_base,
        "DIFY_MODEL_NAME": model,
        "DEEPSEEK_API_KEY": api_key,
    }.items():
        lines = upsert(lines, key, value)
    write_lines(lines)
    print("Validated DeepSeek model variables were imported without displaying secrets.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ensure-admin", action="store_true")
    parser.add_argument("--rotate-admin-password", action="store_true")
    parser.add_argument("--import-model-env", type=Path)
    parser.add_argument("--set-from-stdin")
    args = parser.parse_args()
    if args.ensure_admin:
        ensure_admin()
        return
    if args.rotate_admin_password:
        rotate_admin_password()
        return
    if args.import_model_env:
        import_model_env(args.import_model_env)
        return
    if args.set_from_stdin:
        set_from_stdin(args.set_from_stdin)
        return
    parser.error("Choose --ensure-admin or --set-from-stdin KEY")


if __name__ == "__main__":
    main()
