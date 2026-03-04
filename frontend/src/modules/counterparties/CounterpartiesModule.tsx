import { useEffect, useMemo, useState } from "react";
import { DragEndEvent } from "@dnd-kit/core";

import {
  archiveCounterparty,
  CounterpartyDto,
  CounterpartyFolderDto,
  createCounterparty,
  createCounterpartyFolder,
  getCounterparties,
  getCounterpartyFolders,
  restoreCounterparty,
  updateCounterparty,
  updateCounterpartyFolder,
} from "../../api/counterparties";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";
import CounterpartiesToolbar from "./CounterpartiesToolbar";
import CounterpartiesTree, { SelectedTreeNode, TreeNode } from "./CounterpartiesTree";
import CounterpartyViewer from "./CounterpartyViewer";
import CreateCounterpartyModal from "./CreateCounterpartyModal";
import CreateFolderModal from "./CreateFolderModal";

const CounterpartiesModule = (_: ModuleRuntimeProps) => {
  const { token } = useAuth();
  const [folders, setFolders] = useState<CounterpartyFolderDto[]>([]);
  const [counterparties, setCounterparties] = useState<CounterpartyDto[]>([]);
  const [selectedNode, setSelectedNode] = useState<SelectedTreeNode>({ type: "root" });
  const [expandedFolders, setExpandedFolders] = useState<Record<number, boolean>>({});
  const [showArchive, setShowArchive] = useState(false);
  const [search, setSearch] = useState("");
  const [showCounterpartyModal, setShowCounterpartyModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [editingCounterparty, setEditingCounterparty] = useState<CounterpartyDto | null>(null);

  const loadAll = async () => {
    if (!token) return;
    const [nextFolders, nextCounterparties] = await Promise.all([getCounterpartyFolders(token), getCounterparties(token, true)]);
    setFolders(nextFolders.map((folder) => ({ ...folder, sort_order: folder.sort_order ?? 0 })));
    setCounterparties(nextCounterparties.map((counterparty) => ({ ...counterparty, sort_order: counterparty.sort_order ?? 0 })));
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
      if (!showArchive && (item.is_archived || item.status === "archived")) return false;
      if (!query) return true;
      return [item.name, item.legal_name, item.city, item.product_group].some((value) => value?.toLowerCase().includes(query));
    });
  }, [counterparties, search, showArchive]);

  const selectedCounterparty = useMemo(() => {
    if (selectedNode.type !== "counterparty") return null;
    return counterparties.find((item) => item.id === selectedNode.id) ?? null;
  }, [counterparties, selectedNode]);

  const selectedFolder = useMemo(() => {
    if (selectedNode.type !== "folder") return null;
    return folders.find((item) => item.id === selectedNode.id) ?? null;
  }, [folders, selectedNode]);

  const folderContents = useMemo(() => {
    const parentId = selectedNode.type === "folder" ? selectedNode.id : null;
    return {
      folders: folders.filter((item) => item.parent_id === parentId),
      counterparties: visibleCounterparties.filter((item) => item.folder_id === parentId),
    };
  }, [folders, selectedNode, visibleCounterparties]);

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
      setSelectedNode({ type: "counterparty", id: editingCounterparty.id });
    } else {
      const created = await createCounterparty(token, payload);
      setSelectedNode({ type: "counterparty", id: created.id });
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
        .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id - b.id);
      const sortOrder = siblingFolders.length;
      await updateCounterpartyFolder(token, activeNode.folder.id, { parent_id: parentId, sort_order: sortOrder });
      await loadAll();
      return;
    }

    const moved = activeNode.counterparty;
    const parentFolderId = overNode.type === "root" ? null : overNode.type === "folder" ? overNode.folder.id : overNode.counterparty.folder_id;
    const siblings = counterparties
      .filter((item) => item.id !== moved.id && item.folder_id === parentFolderId)
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id - b.id);
    const sortOrder = siblings.length;

    await updateCounterparty(token, moved.id, { ...moved, folder_id: parentFolderId, sort_order: sortOrder });
    await loadAll();
  };

  const toggleArchive = async () => {
    if (!token || !selectedCounterparty) return;
    if (selectedCounterparty.status === "archived" || selectedCounterparty.is_archived) {
      await restoreCounterparty(token, selectedCounterparty.id);
    } else {
      await archiveCounterparty(token, selectedCounterparty.id);
    }
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
          selectedNode={selectedNode}
          expandedFolders={expandedFolders}
          onToggleFolder={(folderId) => setExpandedFolders((prev) => ({ ...prev, [folderId]: !prev[folderId] }))}
          onSelectRoot={() => setSelectedNode({ type: "root" })}
          onSelectFolder={(folderId) => setSelectedNode({ type: "folder", id: folderId })}
          onSelectCounterparty={(counterpartyId) => setSelectedNode({ type: "counterparty", id: counterpartyId })}
          onDragEnd={(event, nodes) => void onDragEnd(event, nodes)}
        />
        <CounterpartyViewer
          mode={selectedNode.type === "counterparty" ? "counterparty" : "folder"}
          counterparty={selectedCounterparty}
          folder={selectedFolder}
          folders={folders}
          contentFolders={folderContents.folders}
          contentCounterparties={folderContents.counterparties}
          showArchive={showArchive}
          onEdit={() => {
            if (!selectedCounterparty) return;
            setEditingCounterparty(selectedCounterparty);
            setShowCounterpartyModal(true);
          }}
          onToggleArchive={() => void toggleArchive()}
          onSelectCounterparty={(counterpartyId) => setSelectedNode({ type: "counterparty", id: counterpartyId })}
          onSelectFolder={(folderId) => setSelectedNode({ type: "folder", id: folderId })}
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
