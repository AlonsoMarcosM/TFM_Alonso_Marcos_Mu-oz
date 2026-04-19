import { OperationCard } from "./OperationCard";

import type { Operation } from "@/server/operations";

export function OperationGrid({ operations }: { operations: Operation[] }) {
  return (
    <div className="grid">
      {operations.map((operation) => (
        <OperationCard key={operation.id} operation={operation} />
      ))}
    </div>
  );
}
