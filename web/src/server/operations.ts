export type OperationId =
  | "check-prereqs"
  | "status-infra"
  | "backup-openmetadata-state"
  | "restore-openmetadata-state"
  | "deploy-postgres-k8s"
  | "launch-infra"
  | "delete-cluster-preserve-state"
  | "reset-poc-clean"
  | "run-full-flow"
  | "ingest-postgres"
  | "bootstrap-governance"
  | "validate-governance-sheet"
  | "workflow-dry-run"
  | "workflow-apply"
  | "export-dcat"
  | "validate-dcat"
  | "validate-runtime"
  | "run-validation-suite"
  | "validate-live-dcat";

export type Operation = {
  id: OperationId;
  title: string;
  group: "Infraestructura" | "Ingesta" | "Gobierno" | "Workflow" | "DCAT" | "Runtime" | "Validacion";
  description: string;
  command: string;
  args: string[];
  artifacts: string[];
  timeoutMs: number;
  requiresOpenMetadataToken?: boolean;
  risk?: string;
  confirmText?: string;
};

const python = "python";
const powershell = "powershell";

export const operations: Operation[] = [
  {
    id: "check-prereqs",
    title: "Comprobar prerrequisitos",
    group: "Infraestructura",
    description: "Valida herramientas locales necesarias para la PoC con el script estricto del repositorio.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\check_prereqs.ps1", "-Strict"],
    artifacts: [],
    timeoutMs: 120_000,
  },
  {
    id: "status-infra",
    title: "Estado de infraestructura",
    group: "Infraestructura",
    description: "Muestra contexto Kubernetes, releases Helm, pods, servicios y PostgreSQL demo.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\status_infra.ps1"],
    artifacts: [],
    timeoutMs: 120_000,
  },
  {
    id: "backup-openmetadata-state",
    title: "Backup estado OpenMetadata",
    group: "Infraestructura",
    description: "Guarda un snapshot SQL local del estado de OpenMetadata antes de resetear o recrear la demo.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\backup_openmetadata_state.ps1"],
    artifacts: ["state/openmetadata/mysql/openmetadata_db.sql"],
    timeoutMs: 300_000,
  },
  {
    id: "restore-openmetadata-state",
    title: "Restaurar estado OpenMetadata",
    group: "Infraestructura",
    description: "Restaura el snapshot SQL local sobre MySQL de OpenMetadata.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\restore_openmetadata_state.ps1"],
    artifacts: ["state/openmetadata/mysql/openmetadata_db.sql"],
    timeoutMs: 300_000,
    risk: "Sobrescribe el estado actual de OpenMetadata con el snapshot local.",
    confirmText: "Restaurar snapshot de OpenMetadata sobre el estado actual?",
  },
  {
    id: "deploy-postgres-k8s",
    title: "Desplegar PostgreSQL demo",
    group: "Infraestructura",
    description: "Aplica los manifiestos del PostgreSQL dummy dentro del cluster Kubernetes.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\deploy_postgres_k8s.ps1"],
    artifacts: [],
    timeoutMs: 300_000,
  },
  {
    id: "launch-infra",
    title: "Levantar infraestructura",
    group: "Infraestructura",
    description: "Crea o actualiza kind, PostgreSQL, dependencias Helm y OpenMetadata usando los scripts canónicos.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\launch_infra.ps1"],
    artifacts: [],
    timeoutMs: 2_700_000,
  },
  {
    id: "delete-cluster-preserve-state",
    title: "Reset infraestructura conservando estado",
    group: "Infraestructura",
    description: "Hace backup del estado de OpenMetadata y elimina el cluster kind para poder recrearlo después.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\delete_cluster_preserve_state.ps1"],
    artifacts: ["state/openmetadata/mysql/openmetadata_db.sql"],
    timeoutMs: 600_000,
    risk: "Elimina el cluster kind completo. Antes intenta dejar snapshot local de OpenMetadata.",
    confirmText: "Eliminar el cluster kind y conservar snapshot local?",
  },
  {
    id: "reset-poc-clean",
    title: "Reset limpio y recrear PoC",
    group: "Infraestructura",
    description: "Elimina el cluster, aparta el snapshot para no restaurar datos anteriores y ejecuta el flujo completo.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\reset_poc_clean.ps1", "-RunFullFlow", "-SkipPipInstall"],
    artifacts: ["tmp_pytest/workflow_first_plan.json"],
    timeoutMs: 3_600_000,
    risk: "Recrea la PoC desde infraestructura limpia. Los datos activos del cluster se eliminan; el snapshot previo se archiva si existe.",
    confirmText: "Resetear infraestructura y datos para recrear la PoC limpia?",
  },
  {
    id: "run-full-flow",
    title: "Flujo completo reproducible",
    group: "Infraestructura",
    description: "Ejecuta launch_infra, ingesta PostgreSQL, bootstrap de gobierno y dry-run del workflow.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\run_full_flow.ps1", "-SkipPipInstall"],
    artifacts: ["tmp_pytest/workflow_first_plan.json"],
    timeoutMs: 3_600_000,
  },
  {
    id: "ingest-postgres",
    title: "Ingestar PostgreSQL demo",
    group: "Ingesta",
    description: "Crea o verifica el servicio postgres_demo_service en OpenMetadata y ejecuta la ingesta técnica.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\ingest_postgres.ps1"],
    artifacts: [],
    timeoutMs: 900_000,
  },
  {
    id: "bootstrap-governance",
    title: "Preparar tags y custom properties",
    group: "Ingesta",
    description: "Crea o verifica tags DCAT y custom properties necesarios antes del workflow de gobierno.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\bootstrap_governance_from_env.ps1", "-SkipPipInstall"],
    artifacts: [],
    timeoutMs: 180_000,
  },
  {
    id: "validate-governance-sheet",
    title: "Validar hoja gold",
    group: "Gobierno",
    description: "Comprueba el contrato funcional de gold_governance.csv con las reglas Python existentes.",
    command: python,
    args: ["-m", "om_dcat_sync", "validate-governance-sheet", "--sheet", ".\\tfm_ingestor\\config\\gold_governance.csv"],
    artifacts: ["tfm_ingestor/config/gold_governance.csv"],
    timeoutMs: 60_000,
  },
  {
    id: "workflow-dry-run",
    title: "Dry-run del workflow",
    group: "Workflow",
    description: "Genera el plan sin aplicar cambios sobre OpenMetadata.",
    command: python,
    args: ["-m", "om_dcat_sync", "workflow", "run", "--dry-run", "--plan-output", ".\\tmp_pytest\\web_workflow_plan.json"],
    artifacts: ["tmp_pytest/web_workflow_plan.json"],
    timeoutMs: 180_000,
    requiresOpenMetadataToken: true,
  },
  {
    id: "workflow-apply",
    title: "Aplicar workflow",
    group: "Workflow",
    description: "Aplica el gobierno y ejecuta exportación y validación según el perfil operativo.",
    command: python,
    args: ["-m", "om_dcat_sync", "workflow", "run", "--allow-warnings", "--export-output", ".\\tmp_pytest\\web_catalog.jsonld", "--report-output", ".\\tmp_pytest\\web_shacl_report.ttl"],
    artifacts: ["tmp_pytest/web_catalog.jsonld", "tmp_pytest/web_shacl_report.ttl"],
    timeoutMs: 240_000,
    requiresOpenMetadataToken: true,
  },
  {
    id: "export-dcat",
    title: "Exportar DCAT",
    group: "DCAT",
    description: "Exporta el catálogo OpenMetadata a JSON-LD DCAT-AP-ES.",
    command: python,
    args: ["-m", "om_dcat_sync", "export-dcat", "--output", ".\\tmp_pytest\\web_catalog.jsonld"],
    artifacts: ["tmp_pytest/web_catalog.jsonld"],
    timeoutMs: 180_000,
    requiresOpenMetadataToken: true,
  },
  {
    id: "validate-dcat",
    title: "Validar DCAT",
    group: "DCAT",
    description: "Valida el JSON-LD exportado contra las SHACL locales congeladas.",
    command: python,
    args: ["-m", "om_dcat_sync", "validate-dcat", "--input", ".\\tmp_pytest\\web_catalog.jsonld", "--profile-case", "hvd", "--allow-warnings", "--report-output", ".\\tmp_pytest\\web_shacl_report.ttl"],
    artifacts: ["tmp_pytest/web_catalog.jsonld", "tmp_pytest/web_shacl_report.ttl"],
    timeoutMs: 180_000,
    requiresOpenMetadataToken: true,
  },
  {
    id: "validate-runtime",
    title: "Validar estado vivo",
    group: "Runtime",
    description: "Comprueba el estado técnico y de gobierno frente al contrato de demo.",
    command: python,
    args: ["-m", "om_dcat_sync", "validate-runtime", "--strict", "--output", ".\\tmp_pytest\\web_runtime_report.json"],
    artifacts: ["tmp_pytest/web_runtime_report.json"],
    timeoutMs: 180_000,
    requiresOpenMetadataToken: true,
  },
  {
    id: "run-validation-suite",
    title: "Suite completa",
    group: "Validacion",
    description: "Ejecuta la suite versionada de validación de la PoC.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\run_validation_suite.ps1"],
    artifacts: ["tmp_pytest/validation_suite_summary.json", "tmp_pytest/validation_suite_catalog.jsonld", "tmp_pytest/validation_suite_shacl_report.ttl"],
    timeoutMs: 900_000,
  },
  {
    id: "validate-live-dcat",
    title: "Validar DCAT live",
    group: "Validacion",
    description: "Ejecuta el script existente de validación live DCAT.",
    command: powershell,
    args: ["-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\infra\\validate_live_dcat.ps1"],
    artifacts: ["tmp_pytest/live_dcat_catalog.jsonld", "tmp_pytest/live_dcat_validation_report.ttl"],
    timeoutMs: 300_000,
  },
];

export const excludedOperations = [
  "scripts/planning/bootstrap_github_project.py",
  "scripts/planning/github_project_mvp.json",
  "scripts/infra/port_forward_openmetadata.ps1",
  "scripts/infra/generate_om_jwt.py",
];

export function findOperation(id: string): Operation | undefined {
  return operations.find((operation) => operation.id === id);
}

export function displayCommand(operation: Operation): string {
  return [operation.command, ...operation.args].join(" ");
}
