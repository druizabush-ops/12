import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import { CounterpartyDto } from "../../api/counterparties";

type Props = {
  items: CounterpartyDto[];
  selectedCounterpartyId: number | null;
  onSelect: (counterpartyId: number) => void;
};

const DraggableRow = ({ item, isSelected, onSelect }: { item: CounterpartyDto; isSelected: boolean; onSelect: () => void }) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useDraggable({ id: `counterparty-${item.id}` });
  const isArchived = item.status === "archived" || item.is_archived;
  const rowBackground = isSelected
    ? "var(--accent-soft)"
    : isArchived
      ? "color-mix(in srgb, var(--danger) 12%, transparent)"
      : "transparent";

  return (
    <tr style={{ background: rowBackground, color: isArchived ? "var(--danger)" : "inherit" }} onClick={onSelect}>
      <td style={{ padding: "8px 6px" }}>
        <span ref={setNodeRef} {...attributes} {...listeners} style={{ transform: CSS.Transform.toString(transform), transition, cursor: "grab" }}>⋮⋮</span> {item.name}
      </td>
      <td>{item.status}</td>
    </tr>
  );
};

const FolderCounterpartiesList = ({ items, selectedCounterpartyId, onSelect }: Props) => (
  <section className="admin-card">
    {items.length === 0 ? (
      <p style={{ color: "var(--text-secondary)", margin: 0 }}>Нет контрагентов в выбранной папке.</p>
    ) : (
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Наименование</th>
            <th align="left">Статус</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <DraggableRow key={item.id} item={item} isSelected={selectedCounterpartyId === item.id} onSelect={() => onSelect(item.id)} />
          ))}
        </tbody>
      </table>
    )}
  </section>
);

export default FolderCounterpartiesList;
