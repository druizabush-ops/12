import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";
import { ReactNode } from "react";

type FolderNodeProps = {
  id: string;
  depth: number;
  name: string;
  isSelected: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect: () => void;
  children?: ReactNode;
};

const FolderNode = ({ id, depth, name, isSelected, isExpanded, onToggle, onSelect, children }: FolderNodeProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isOver } = useSortable({ id });
  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        borderRadius: 10,
        background: isOver ? "var(--accent-soft)" : "transparent",
        border: `1px solid ${isOver ? "var(--accent)" : "transparent"}`,
      }}
    >
      <div style={{ paddingLeft: depth * 16, display: "flex", gap: 8, alignItems: "center" }}>
        <button type="button" className="ghost-button" onClick={onToggle}>{isExpanded ? "▾" : "▸"}</button>
        <button
          type="button"
          className="ghost-button"
          onClick={onSelect}
          style={{ border: "none", fontWeight: isSelected ? 700 : 500 }}
        >
          <span {...attributes} {...listeners} style={{ cursor: "grab" }}>📁 {name}</span>
        </button>
      </div>
      {children}
    </div>
  );
};

export default FolderNode;
