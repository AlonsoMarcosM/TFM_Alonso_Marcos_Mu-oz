const setupCommands = [
  "powershell -ExecutionPolicy Bypass -File .\\scripts\\infra\\launch_infra.ps1",
  "powershell -ExecutionPolicy Bypass -File .\\scripts\\infra\\port_forward_openmetadata.ps1",
  "cd .\\web && npm install && npm run dev",
];

const future = [
  "Autenticación y permisos",
  "GitHub Project",
  "Edición avanzada de YAML",
  "Nuevos datasets dinámicos",
  "Base de datos propia",
];

export default function PreparacionPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Preparación de demo</h1>
        <p className="lead">
          Estos comandos preparan el entorno base. La gestión de infraestructura y reset ya está disponible como
          botones dentro del menú Infraestructura.
        </p>
      </header>
      <section className="panel">
        <h2>Comandos previos</h2>
        {setupCommands.map((command) => (
          <code className="command" key={command}>{command}</code>
        ))}
      </section>
      <section className="panel">
        <h2>Fuera de alcance para esta demo</h2>
        <ul>
          {future.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
