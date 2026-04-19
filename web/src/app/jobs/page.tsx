import { JobsList } from "@/components/JobsList";

export default function JobsPage() {
  return (
    <div className="stack">
      <header>
        <h1 className="page-title">Ejecuciones</h1>
        <p className="lead">Historial local de ejecuciones lanzadas desde la app.</p>
      </header>
      <JobsList />
    </div>
  );
}
