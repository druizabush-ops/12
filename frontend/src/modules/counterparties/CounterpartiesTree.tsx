import { useMemo } from "react";

import { CounterpartyFolderDto } from "../../api/counterparties";
import FolderNode from "./FolderNode";
import RootNode from "./RootNode";

type CounterpartiesTreeProps = {
  folders: CounterpartyFolderDto[];
  rootFolderId: number;
  selectedFolderId: number;
  expandedFolders: Record<number, boolean>;
  onToggleFolder: (folderId: number) => void;
  onSelectFolder: (folderId: number) => void;
};

const CounterpartiesTree = ({
  folders,
  rootFolderId,
  selectedFolderId,
  expandedFolders,
  onToggleFolder,
  onSelectFolder
}: CounterpartiesTreeProps) => {
  const folderByParent = useMemo(() => {
    const map = new Map<number, CounterpartyFolderDto[]>();
    folders.forEach((folder) => {
      if (folder.id === rootFolderId) return;
      const list = map.get(folder.parent_id ?? rootFolderId) ?? [];
      list.push(folder);
      map.set(folder.parent_id ?? rootFolderId, list);
    });
    return map;
  }, [folders, rootFolderId]);

  const renderFolders = (parentId: number, depth: number): JSX.Element[] => {
    const children = (folderByParent.get(parentId) ?? []).sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id - b.id);
    return children.flatMap((folder) => {
      const isExpanded = Boolean(expandedFolders[folder.id]);
      return [
        <FolderNode
          key={folder.id}
          id={`folder-${folder.id}`}
          depth={depth}
          name={folder.name}
          isSelected={selectedFolderId === folder.id}
          isExpanded={isExpanded}
          onToggle={() => onToggleFolder(folder.id)}
          onSelect={() => onSelectFolder(folder.id)}
        />,
        ...(isExpanded ? renderFolders(folder.id, depth + 1) : []),
      ];
    });
  };

  return (
    <section className="admin-card" style={{ display: "grid", gap: 4 }}>
      <RootNode isSelected={selectedFolderId === rootFolderId} onSelect={() => onSelectFolder(rootFolderId)} />
      {renderFolders(rootFolderId, 1)}
    </section>
  );
};

export default CounterpartiesTree;
