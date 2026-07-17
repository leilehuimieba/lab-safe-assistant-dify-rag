import fs from "node:fs";


const ENV_PATH = "D:/newwork/Security/lab-safe-assistant-dify-rag/.env.dify_rag";


export function updateDifyAppKey(value) {
  if (!/^app-[A-Za-z0-9_-]{20,}$/.test(value)) {
    throw new Error("Value does not look like a Dify App API key.");
  }
  const original = fs.existsSync(ENV_PATH)
    ? fs.readFileSync(ENV_PATH, "utf8")
    : "";
  const lines = original.split(/\r?\n/).filter((line, index, all) => {
    return !(index === all.length - 1 && line === "");
  });
  const rendered = `DIFY_APP_API_KEY=${value}`;
  const index = lines.findIndex((line) => /^\s*DIFY_APP_API_KEY\s*=/.test(line));
  if (index >= 0) {
    lines[index] = rendered;
  } else {
    lines.push(rendered);
  }
  fs.writeFileSync(ENV_PATH, `${lines.join("\n").replace(/\n+$/, "")}\n`, {
    encoding: "utf8",
    mode: 0o600,
  });
}
