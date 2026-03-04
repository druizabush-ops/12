import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";
import { ReactNode } from "react";

type FolderNodeProps = {
  id: string;
  depth: number;
  name: string;
  isExpanded: boolean;
  onToggle: () => void;
  children?: ReactNode;
};

const FolderNode = ({ id, depth, name, isExpanded, onToggle, children }: FolderNodeProps) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  return (
    <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition }}>
      <div style={{ paddingLeft: depth * 16, display: "flex", gap: 8, alignItems: "center" }}>
        <button type="button" className="ghost-button" onClick={onToggle}>{isExpanded ? "▾" : "▸"}</button>
        <span {...attributes} {...listeners} style={{ cursor: "grab" }}>📁 {name}</span>
      </div>
      {children}
    </div>
  );
};

export default FolderNode;
