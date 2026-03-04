import { useDroppable } from "@dnd-kit/core";

type RootNodeProps = {
  isSelected: boolean;
  onSelect: () => void;
};

const RootNode = ({ isSelected, onSelect }: RootNodeProps) => {
  const { setNodeRef, isOver } = useDroppable({ id: "root-folder-drop" });

  return (
    <button
      ref={setNodeRef}
      type="button"
      className="ghost-button"
      style={{
        justifyContent: "flex-start",
        fontWeight: isSelected ? 700 : 500,
        background: isOver ? "var(--accent-soft)" : "transparent",
        borderColor: isOver ? "var(--accent)" : "var(--border)",
      }}
      onClick={onSelect}
    >
      📁 Каталог
    </button>
  );
};

export default RootNode;
