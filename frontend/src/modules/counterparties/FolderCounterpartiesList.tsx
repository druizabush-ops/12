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

  return (
    <tr style={{ background: isSelected ? "var(--accent-soft)" : "transparent" }} onClick={onSelect}>
      <td style={{ padding: "8px 6px" }}>
        <span ref={setNodeRef} {...attributes} {...listeners} style={{ transform: CSS.Transform.toString(transform), transition, cursor: "grab" }}>⋮⋮</span> {item.name}
      </td>
      <td>{item.city || "—"}</td>
      <td>{item.phone || "—"}</td>
      <td>{item.status}</td>
    </tr>
  );
};

const FolderCounterpartiesList = ({ items, selectedCounterpartyId, onSelect }: Props) => (
  <section className="admin-card" style={{ maxHeight: "74vh", overflow: "auto" }}>
    <h3 style={{ marginTop: 0 }}>Содержимое папки</h3>
    {items.length === 0 ? (
      <p style={{ color: "var(--text-secondary)" }}>Нет контрагентов в выбранной папке.</p>
    ) : (
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Наименование</th>
            <th align="left">Город</th>
            <th align="left">Телефон</th>
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
