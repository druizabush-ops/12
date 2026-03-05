import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

type FolderNodeProps = {
  id: string;
  depth: number;
  name: string;
  isSelected: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect: () => void;
};

const FolderNode = ({ id, depth, name, isSelected, isExpanded, onToggle, onSelect }: FolderNodeProps) => {
  const { setNodeRef: setDropRef, isOver } = useDroppable({ id });
  const { attributes, listeners, setNodeRef: setDragRef, transform, transition } = useDraggable({ id });

  return (
    <div
      ref={setDropRef}
      style={{
        paddingLeft: depth * 14,
        borderRadius: 10,
        background: isOver || isSelected ? "var(--accent-soft)" : "transparent",
        border: `1px solid ${isOver || isSelected ? "var(--accent)" : "transparent"}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <button type="button" className="ghost-button" onClick={onToggle}>{isExpanded ? "▾" : "▸"}</button>
        <button type="button" className="ghost-button" onClick={onSelect} style={{ fontWeight: isSelected ? 700 : 500 }}>
          📁 {name}
        </button>
        <span
          ref={setDragRef}
          {...attributes}
          {...listeners}
          style={{ transform: CSS.Transform.toString(transform), transition, cursor: "grab", color: "var(--text-secondary)" }}
        >
          ⋮⋮
        </span>
      </div>
    </div>
  );
};

export default FolderNode;
