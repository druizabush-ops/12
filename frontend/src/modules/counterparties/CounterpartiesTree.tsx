import { DragEndEvent, DndContext, PointerSensor, closestCenter, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useMemo } from "react";

import { CounterpartyDto, CounterpartyFolderDto } from "../../api/counterparties";
import CounterpartyNode from "./CounterpartyNode";
import FolderNode from "./FolderNode";
import RootNode from "./RootNode";

export type TreeNode =
  | { id: "root"; type: "root"; depth: number }
  | { id: string; type: "folder"; depth: number; folder: CounterpartyFolderDto }
  | { id: string; type: "counterparty"; depth: number; counterparty: CounterpartyDto };

export type SelectedTreeNode = { type: "root" } | { type: "folder"; id: number } | { type: "counterparty"; id: number };

type CounterpartiesTreeProps = {
  folders: CounterpartyFolderDto[];
  counterparties: CounterpartyDto[];
  selectedNode: SelectedTreeNode;
  expandedFolders: Record<number, boolean>;
  onToggleFolder: (folderId: number) => void;
  onSelectRoot: () => void;
  onSelectFolder: (folderId: number) => void;
  onSelectCounterparty: (counterpartyId: number) => void;
  onDragEnd: (event: DragEndEvent, visibleNodes: TreeNode[]) => void;
};

const CounterpartiesTree = ({
  folders,
  counterparties,
  selectedNode,
  expandedFolders,
  onToggleFolder,
  onSelectRoot,
  onSelectFolder,
  onSelectCounterparty,
  onDragEnd,
}: CounterpartiesTreeProps) => {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const visibleNodes = useMemo(() => {
    const byParent = new Map<number | null, CounterpartyFolderDto[]>();
    const byFolder = new Map<number | null, CounterpartyDto[]>();

    folders.forEach((folder) => {
      const list = byParent.get(folder.parent_id) ?? [];
      list.push(folder);
      byParent.set(folder.parent_id, list);
    });

    counterparties.forEach((counterparty) => {
      const list = byFolder.get(counterparty.folder_id) ?? [];
      list.push(counterparty);
      byFolder.set(counterparty.folder_id, list);
    });

    const nodes: TreeNode[] = [];

    const safeSortOrder = (value: number | null) => value ?? 0;

    const walk = (parentId: number | null, depth: number) => {
      const currentFolders = (byParent.get(parentId) ?? []).sort((a, b) => safeSortOrder(a.sort_order) - safeSortOrder(b.sort_order) || a.id - b.id);
      currentFolders.forEach((folder) => {
        nodes.push({ id: `folder-${folder.id}`, type: "folder", depth, folder });
        if (!expandedFolders[folder.id]) return;
        walk(folder.id, depth + 1);
        const folderCounterparties = (byFolder.get(folder.id) ?? []).sort(
          (a, b) => safeSortOrder(a.sort_order) - safeSortOrder(b.sort_order) || a.id - b.id,
        );
        folderCounterparties.forEach((counterparty) => {
          nodes.push({ id: `counterparty-${counterparty.id}`, type: "counterparty", depth: depth + 1, counterparty });
        });
      });
    };

    nodes.push({ id: "root", type: "root", depth: 0 });
    walk(null, 1);

    const rootCounterparties = (byFolder.get(null) ?? []).sort((a, b) => safeSortOrder(a.sort_order) - safeSortOrder(b.sort_order) || a.id - b.id);
    rootCounterparties.forEach((counterparty) => {
      nodes.push({ id: `counterparty-${counterparty.id}`, type: "counterparty", depth: 1, counterparty });
    });

    return nodes;
  }, [counterparties, expandedFolders, folders]);

  return (
    <section className="admin-card" style={{ maxHeight: "75vh", overflow: "auto" }}>
      <h3>Каталог</h3>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => onDragEnd(event, visibleNodes)}>
        <SortableContext items={visibleNodes.filter((item) => item.type !== "root").map((item) => item.id)} strategy={verticalListSortingStrategy}>
          <div style={{ display: "grid", gap: 4 }}>
            {visibleNodes.map((node) => {
              if (node.type === "root") {
                return (
                  <RootNode
                    key={node.id}
                    isSelected={selectedNode.type === "root"}
                    onSelect={onSelectRoot}
                  />
                );
              }

              if (node.type === "folder") {
                return (
                  <FolderNode
                    key={node.id}
                    id={node.id}
                    depth={node.depth}
                    name={node.folder.name}
                    isSelected={selectedNode.type === "folder" && selectedNode.id === node.folder.id}
                    isExpanded={Boolean(expandedFolders[node.folder.id])}
                    onToggle={() => onToggleFolder(node.folder.id)}
                    onSelect={() => onSelectFolder(node.folder.id)}
                  />
                );
              }

              return (
                <CounterpartyNode
                  key={node.id}
                  id={node.id}
                  depth={node.depth}
                  name={node.counterparty.name}
                  isSelected={selectedNode.type === "counterparty" && selectedNode.id === node.counterparty.id}
                  isArchived={node.counterparty.is_archived}
                  onSelect={() => onSelectCounterparty(node.counterparty.id)}
                />
              );
            })}
          </div>
        </SortableContext>
      </DndContext>
    </section>
  );
};

export default CounterpartiesTree;
