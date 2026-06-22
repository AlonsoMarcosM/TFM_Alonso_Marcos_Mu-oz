import fs from "node:fs";
import { spawnSync } from "node:child_process";
import dotenv from "dotenv";

import { isDemoMode } from "./demo";
import { repoPath, repoRoot } from "./repoPaths";

let loaded = false;

export function loadRepoEnv(): void {
  if (loaded) {
    return;
  }
  const envPath = repoPath(".env");
  if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath, override: false, quiet: true });
  }
  loaded = true;
}

export function envStatus() {
  // En demo no hay `.env` ni infraestructura: se reporta el estado de la
  // ejecucion real congelada para que la UI no aparente estar incompleta.
  if (isDemoMode()) {
    return {
      path: "(modo demo, datos congelados)",
      exists: true,
      demo: true,
      required: [
        { name: "OPENMETADATA_BASE_URL", present: true },
        { name: "OPENMETADATA_JWT_TOKEN u OPENMETADATA_TOKEN", present: true },
      ],
    };
  }
  loadRepoEnv();
  const envPath = repoPath(".env");
  return {
    path: envPath,
    exists: fs.existsSync(envPath),
    required: [
      {
        name: "OPENMETADATA_BASE_URL",
        present: Boolean(process.env.OPENMETADATA_BASE_URL && process.env.OPENMETADATA_BASE_URL.trim()),
      },
      {
        name: "OPENMETADATA_JWT_TOKEN u OPENMETADATA_TOKEN",
        present: Boolean(
          (process.env.OPENMETADATA_JWT_TOKEN && process.env.OPENMETADATA_JWT_TOKEN.trim()) ||
            (process.env.OPENMETADATA_TOKEN && process.env.OPENMETADATA_TOKEN.trim()),
        ),
      },
    ],
  };
}

export function jobEnvironment(options: { ensureOpenMetadataToken?: boolean } = {}): NodeJS.ProcessEnv {
  loadRepoEnv();
  const env = { ...process.env };
  if (!env.OPENMETADATA_JWT_TOKEN && env.OPENMETADATA_TOKEN) {
    env.OPENMETADATA_JWT_TOKEN = env.OPENMETADATA_TOKEN;
  }
  if (options.ensureOpenMetadataToken && !env.OPENMETADATA_JWT_TOKEN && !isDemoMode()) {
    const generated = spawnSync("python", [repoPath("scripts", "infra", "generate_om_jwt.py"), "--ttl-hours", "2"], {
      cwd: repoRoot(),
      encoding: "utf8",
      env,
      windowsHide: true,
    });
    if (generated.status === 0 && generated.stdout.trim()) {
      env.OPENMETADATA_JWT_TOKEN = generated.stdout.trim();
    }
  }
  return env;
}
