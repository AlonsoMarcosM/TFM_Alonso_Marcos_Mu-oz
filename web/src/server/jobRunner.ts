import { spawn } from "node:child_process";
import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";

import { isDemoMode } from "./demo";
import { jobEnvironment } from "./env";
import { buildJobResult, type JobResult } from "./jobResult";
import { displayCommand, findOperation, type Operation, type OperationId } from "./operations";
import { redactSecrets } from "./redactSecrets";
import { repoPath, repoRoot } from "./repoPaths";

export type JobStatus = "pending" | "running" | "success" | "error";

export type JobRecord = {
  id: string;
  operationId: OperationId;
  title: string;
  command: string;
  status: JobStatus;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  exitCode?: number | null;
  error?: string;
  log: string;
  artifacts: string[];
  result?: JobResult;
};

const runningJobs = new Map<string, ReturnType<typeof spawn>>();

function jobsDir(): string {
  return repoPath("state", "web_jobs");
}

function jobPath(id: string): string {
  return path.join(jobsDir(), `${id}.json`);
}

async function ensureJobsDir(): Promise<void> {
  // En demo el directorio de jobs es de solo lectura (fixtures versionados); no
  // se crea ni se escribe nada (el FS de Vercel es de solo lectura).
  if (isDemoMode()) {
    return;
  }
  await fsp.mkdir(jobsDir(), { recursive: true });
}

async function writeJob(job: JobRecord): Promise<void> {
  await ensureJobsDir();
  await fsp.writeFile(jobPath(job.id), JSON.stringify(job, null, 2), "utf8");
}

async function readJobFile(filePath: string): Promise<JobRecord | null> {
  try {
    return JSON.parse(await fsp.readFile(filePath, "utf8")) as JobRecord;
  } catch {
    return null;
  }
}

export async function readJob(id: string): Promise<JobRecord | null> {
  const safeId = id.replace(/[^a-zA-Z0-9_-]/g, "");
  if (!safeId || safeId !== id) {
    return null;
  }
  return readJobFile(jobPath(id));
}

export async function listJobs(): Promise<JobRecord[]> {
  await ensureJobsDir();
  const files = await fsp.readdir(jobsDir());
  const jobs = await Promise.all(
    files
      .filter((file) => file.endsWith(".json"))
      .map((file) => readJobFile(path.join(jobsDir(), file))),
  );
  return jobs
    .filter((job): job is JobRecord => Boolean(job))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

function artifactsWithExistence(operation: Operation): string[] {
  return operation.artifacts.filter((artifact) => fs.existsSync(repoPath(...artifact.split("/"))));
}

function demoJob(operation: Operation): JobRecord {
  const now = new Date().toISOString();
  const job: JobRecord = {
    id: randomUUID(),
    operationId: operation.id,
    title: operation.title,
    command: displayCommand(operation),
    status: "success",
    createdAt: now,
    startedAt: now,
    finishedAt: now,
    exitCode: 0,
    log:
      "Modo demo (solo lectura): la ejecucion real contra OpenMetadata y Kubernetes esta deshabilitada.\n" +
      "Este resultado reproduce los artefactos congelados de una ejecucion real previa del caso de uso.\n",
    artifacts: artifactsWithExistence(operation),
  };
  job.result = buildJobResult(operation, job);
  return job;
}

export async function startJob(operationId: string): Promise<JobRecord> {
  const operation = findOperation(operationId);
  if (!operation) {
    throw new Error(`Operacion no permitida: ${operationId}`);
  }

  // En demo no se lanza ningun proceso: se devuelve un job ya finalizado que
  // resume los artefactos congelados. Al entregarse en estado "success" el
  // cliente no hace polling (solo sondea jobs pending/running).
  if (isDemoMode()) {
    return demoJob(operation);
  }

  const id = randomUUID();
  const env = jobEnvironment({ ensureOpenMetadataToken: Boolean(operation.requiresOpenMetadataToken) });
  const job: JobRecord = {
    id,
    operationId: operation.id,
    title: operation.title,
    command: displayCommand(operation),
    status: "pending",
    createdAt: new Date().toISOString(),
    log: "",
    artifacts: operation.artifacts,
  };
  await writeJob(job);

  const child = spawn(operation.command, operation.args, {
    cwd: repoRoot(),
    env,
    windowsHide: true,
  });
  runningJobs.set(id, child);

  job.status = "running";
  job.startedAt = new Date().toISOString();
  await writeJob(job);

  const append = async (chunk: Buffer | string) => {
    job.log += redactSecrets(chunk.toString(), env);
    await writeJob(job);
  };

  child.stdout.on("data", (chunk) => {
    void append(chunk);
  });
  child.stderr.on("data", (chunk) => {
    void append(chunk);
  });
  child.on("error", (error) => {
    job.status = "error";
    job.error = error.message;
    job.finishedAt = new Date().toISOString();
    job.result = buildJobResult(operation, job);
    runningJobs.delete(id);
    void writeJob(job);
  });
  child.on("close", (code) => {
    job.exitCode = code;
    job.status = code === 0 ? "success" : "error";
    job.finishedAt = new Date().toISOString();
    job.artifacts = artifactsWithExistence(operation);
    job.result = buildJobResult(operation, job);
    runningJobs.delete(id);
    void writeJob(job);
  });

  setTimeout(() => {
    if (!runningJobs.has(id)) {
      return;
    }
    job.log += `\nTimeout tras ${operation.timeoutMs} ms. Proceso terminado.\n`;
    child.kill();
  }, operation.timeoutMs).unref();

  return job;
}
