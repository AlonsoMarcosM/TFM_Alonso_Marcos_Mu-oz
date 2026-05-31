const setupCommands = [
  "powershell -ExecutionPolicy Bypass -File .\\scripts\\infra\\launch_infra.ps1",
  "powershell -ExecutionPolicy Bypass -File .\\scripts\\infra\\port_forward_openmetadata.ps1",
  "cd .\\web; pnpm install; pnpm dev",
];

const future = [
  "Orquestación diaria con Airflow u otro planificador",
  "Subida automática a un CKAN externo",
  "Envío por correo del informe RDF/SHACL",
  "Informe PDF o HTML además de JSON/TTL",
  "Autenticación, permisos y auditoría avanzada",
];

export default function PreparacionPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Preparación del caso de uso de validación</h1>
        <p className="lead">
          Estos comandos preparan el entorno base. La gestión de infraestructura y reset también está disponible como
          botones dentro del menú Infraestructura; todos invocan scripts versionados del repositorio.
        </p>
      </header>
      <section className="panel">
        <h2>Lectura operativa</h2>
        <p className="muted">
          La preparación deja disponible OpenMetadata, PostgreSQL de referencia y la consola web. A partir de ahí, el
          operador trabaja con botones y evidencias sin construir comandos manuales.
        </p>
      </section>
      <section className="panel">
        <h2>Comandos previos</h2>
        {setupCommands.map((command) => (
          <code className="command" key={command}>{command}</code>
        ))}
      </section>
      <section className="panel">
        <h2>Trabajo futuro fuera de esta iteración</h2>
        <ul>
          {future.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
