import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";

type CounterpartyNodeProps = {
  id: string;
  depth: number;
  name: string;
  isSelected: boolean;
  isArchived: boolean;
  onSelect: () => void;
};

const CounterpartyNode = ({ id, depth, name, isSelected, isArchived, onSelect }: CounterpartyNodeProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isOver } = useSortable({ id });
  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        borderTop: "1px solid var(--border)",
        borderRadius: 8,
        background: isOver ? "var(--accent-soft)" : "transparent",
        borderColor: isOver ? "var(--accent)" : "var(--border)",
        paddingLeft: depth * 16 + 44,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <span {...attributes} {...listeners} style={{ cursor: "grab" }}>⋮⋮</span>
      <button type="button" className="ghost-button" onClick={onSelect} style={{ fontWeight: isSelected ? 700 : 400 }}>
        📄 {name} {isArchived ? "(архив)" : ""}
      </button>
    </div>
  );
};

export default CounterpartyNode;
