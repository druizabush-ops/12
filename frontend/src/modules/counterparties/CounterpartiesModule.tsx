import { useEffect, useMemo, useState } from "react";
import { DragEndEvent } from "@dnd-kit/core";

import {
  CounterpartyDto,
  CounterpartyFolderDto,
  createCounterparty,
  createCounterpartyFolder,
  getCounterparties,
  getCounterpartyFolders,
  updateCounterparty,
  updateCounterpartyFolder,
} from "../../api/counterparties";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";
import CounterpartiesToolbar from "./CounterpartiesToolbar";
import CounterpartiesTree, { TreeNode } from "./CounterpartiesTree";
import CounterpartyViewer from "./CounterpartyViewer";
import CreateCounterpartyModal from "./CreateCounterpartyModal";
import CreateFolderModal from "./CreateFolderModal";

const CounterpartiesModule = (_: ModuleRuntimeProps) => {
  const { token } = useAuth();
  const [folders, setFolders] = useState<CounterpartyFolderDto[]>([]);
  const [counterparties, setCounterparties] = useState<CounterpartyDto[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Record<number, boolean>>({});
  const [showArchive, setShowArchive] = useState(false);
  const [search, setSearch] = useState("");
  const [showCounterpartyModal, setShowCounterpartyModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [editingCounterparty, setEditingCounterparty] = useState<CounterpartyDto | null>(null);

  const loadAll = async () => {
    if (!token) return;
    const [nextFolders, nextCounterparties] = await Promise.all([getCounterpartyFolders(token), getCounterparties(token, true)]);
    setFolders(nextFolders);
    setCounterparties(nextCounterparties);
    setExpandedFolders((prev) => {
      const next = { ...prev };
      nextFolders.forEach((folder) => {
        if (next[folder.id] === undefined) next[folder.id] = true;
      });
      return next;
    });
  };

  useEffect(() => {
    void loadAll();
  }, [token]);

  const visibleCounterparties = useMemo(() => {
    const query = search.trim().toLowerCase();
    return counterparties.filter((item) => {
      if (!showArchive && item.is_archived) return false;
      if (!query) return true;
      return [item.name, item.legal_name, item.city, item.product_group].some((value) => value?.toLowerCase().includes(query));
    });
  }, [counterparties, search, showArchive]);

  const selected = useMemo(() => counterparties.find((item) => item.id === selectedId) ?? null, [counterparties, selectedId]);

  const submitFolder = async (payload: { name: string; parent_id: number | null }) => {
    if (!token) return;
    await createCounterpartyFolder(token, payload);
    setShowFolderModal(false);
    await loadAll();
  };

  const submitCounterparty = async (payload: Partial<CounterpartyDto>) => {
    if (!token) return;
    if (editingCounterparty) {
      await updateCounterparty(token, editingCounterparty.id, payload);
      setSelectedId(editingCounterparty.id);
    } else {
      const created = await createCounterparty(token, payload);
      setSelectedId(created.id);
    }
    setEditingCounterparty(null);
    setShowCounterpartyModal(false);
    await loadAll();
  };

  const isDescendantFolder = (folderId: number, maybeDescendantId: number): boolean => {
    const byId = new Map(folders.map((item) => [item.id, item]));
    let current = byId.get(maybeDescendantId) ?? null;
    while (current) {
      if (current.parent_id === folderId) return true;
      current = current.parent_id ? byId.get(current.parent_id) ?? null : null;
    }
    return false;
  };

  const onDragEnd = async (event: DragEndEvent, visibleNodes: TreeNode[]) => {
    if (!token || !event.over || event.active.id === event.over.id) return;

    const activeNode = visibleNodes.find((node) => node.id === String(event.active.id));
    const overNode = visibleNodes.find((node) => node.id === String(event.over?.id));
    if (!activeNode || !overNode) return;

    if (activeNode.type === "folder") {
      let parentId: number | null = null;
      if (overNode.type === "folder") parentId = overNode.folder.id;
      if (overNode.type === "counterparty") parentId = overNode.counterparty.folder_id;
      if (parentId === activeNode.folder.id || (parentId && isDescendantFolder(activeNode.folder.id, parentId))) return;

      const siblingFolders = folders
        .filter((item) => item.id !== activeNode.folder.id && item.parent_id === parentId)
        .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
      const sortOrder = siblingFolders.length;
      await updateCounterpartyFolder(token, activeNode.folder.id, { parent_id: parentId, sort_order: sortOrder });
      await loadAll();
      return;
    }

    const moved = activeNode.counterparty;
    const parentFolderId = overNode.type === "folder" ? overNode.folder.id : overNode.counterparty.folder_id;
    const siblings = counterparties
      .filter((item) => item.id !== moved.id && item.folder_id === parentFolderId)
      .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
    const sortOrder = siblings.length;

    await updateCounterparty(token, moved.id, { ...moved, folder_id: parentFolderId, sort_order: sortOrder });
    await loadAll();
  };

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <CounterpartiesToolbar
        search={search}
        showArchive={showArchive}
        onSearchChange={setSearch}
        onToggleArchive={() => setShowArchive((prev) => !prev)}
        onCreateCounterparty={() => {
          setEditingCounterparty(null);
          setShowCounterpartyModal(true);
        }}
        onCreateFolder={() => setShowFolderModal(true)}
      />

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16 }}>
        <CounterpartiesTree
          folders={folders}
          counterparties={visibleCounterparties}
          selectedId={selectedId}
          expandedFolders={expandedFolders}
          onToggleFolder={(folderId) => setExpandedFolders((prev) => ({ ...prev, [folderId]: !prev[folderId] }))}
          onSelectCounterparty={setSelectedId}
          onDragEnd={(event, nodes) => void onDragEnd(event, nodes)}
        />
        <CounterpartyViewer
          counterparty={selected}
          folders={folders}
          onEdit={() => {
            if (!selected) return;
            setEditingCounterparty(selected);
            setShowCounterpartyModal(true);
          }}
        />
      </div>

      {showCounterpartyModal ? (
        <CreateCounterpartyModal
          folders={folders}
          initial={editingCounterparty}
          onClose={() => {
            setShowCounterpartyModal(false);
            setEditingCounterparty(null);
          }}
          onSubmit={submitCounterparty}
        />
      ) : null}

      {showFolderModal ? <CreateFolderModal folders={folders} onClose={() => setShowFolderModal(false)} onSubmit={submitFolder} /> : null}
    </div>
  );
};

export default CounterpartiesModule;
