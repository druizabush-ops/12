import { useEffect, useMemo, useState } from "react";
import { DndContext, DragEndEvent } from "@dnd-kit/core";

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
import AutoTasksPanel from "./AutoTasksPanel";
import CounterpartiesToolbar from "./CounterpartiesToolbar";
import CounterpartiesTree from "./CounterpartiesTree";
import CounterpartyViewer from "./CounterpartyViewer";
import CreateCounterpartyModal from "./CreateCounterpartyModal";
import CreateFolderModal from "./CreateFolderModal";
import FolderCounterpartiesList from "./FolderCounterpartiesList";

const ROOT_NAME = "Каталог";
const columnHeaderStyle = { fontWeight: 600, fontSize: 14, marginBottom: 8 };
const columnShellStyle = { display: "flex", flexDirection: "column" as const, minHeight: 0, overflow: "hidden", padding: "0 10px" };

const CounterpartiesModule = (_: ModuleRuntimeProps) => {
  const { token } = useAuth();
  const [folders, setFolders] = useState<CounterpartyFolderDto[]>([]);
  const [counterparties, setCounterparties] = useState<CounterpartyDto[]>([]);
  const [rootFolderId, setRootFolderId] = useState<number | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [selectedCounterpartyId, setSelectedCounterpartyId] = useState<number | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Record<number, boolean>>({});
  const [showArchive, setShowArchive] = useState(false);
  const [search, setSearch] = useState("");
  const [showCounterpartyModal, setShowCounterpartyModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [editingCounterparty, setEditingCounterparty] = useState<CounterpartyDto | null>(null);
  const [cardColors, setCardColors] = useState<Record<number, string>>({});

  useEffect(() => {
    const saved = localStorage.getItem("counterparties-card-colors");
    if (saved) setCardColors(JSON.parse(saved) as Record<number, string>);
  }, []);

  const persistCardColor = (counterpartyId: number, color: string | null) => {
    setCardColors((prev) => {
      const next = { ...prev };
      if (color) next[counterpartyId] = color;
      else delete next[counterpartyId];
      localStorage.setItem("counterparties-card-colors", JSON.stringify(next));
      return next;
    });
  };

  const loadAll = async () => {
    if (!token) return;
    const [loadedFolders, loadedCounterparties] = await Promise.all([getCounterpartyFolders(token), getCounterparties(token, true)]);

    let rootFolder = loadedFolders.find((folder) => folder.name === ROOT_NAME && folder.parent_id === null) ?? null;
    if (!rootFolder) {
      rootFolder = await createCounterpartyFolder(token, { parent_id: null, name: ROOT_NAME, sort_order: 0 });
      loadedFolders.push(rootFolder);
    }

    const folderIds = new Set(loadedFolders.map((item) => item.id));
    const normalizedFolders = loadedFolders.map((folder) => ({
      ...folder,
      sort_order: folder.sort_order ?? 0,
      parent_id: folder.id === rootFolder!.id ? null : folder.parent_id && folderIds.has(folder.parent_id) ? folder.parent_id : rootFolder!.id,
    }));

    setFolders(normalizedFolders);
    setCounterparties(loadedCounterparties.map((item) => ({ ...item, sort_order: item.sort_order ?? 0, folder_id: item.folder_id ?? rootFolder!.id })));
    setRootFolderId(rootFolder.id);
    setSelectedFolderId((prev) => prev ?? rootFolder!.id);
    setExpandedFolders((prev) => {
      const next = { ...prev };
      normalizedFolders.forEach((folder) => {
        if (next[folder.id] === undefined) next[folder.id] = true;
      });
      return next;
    });
  };

  useEffect(() => {
    void loadAll();
  }, [token]);

  const selectedCounterparty = useMemo(() => counterparties.find((item) => item.id === selectedCounterpartyId) ?? null, [counterparties, selectedCounterpartyId]);

  const selectedFolderCounterparties = useMemo(() => {
    if (!selectedFolderId) return [];
    const query = search.trim().toLowerCase();
    return counterparties.filter((item) => {
      if (item.folder_id !== selectedFolderId) return false;
      if (!showArchive && (item.is_archived || item.status === "archived")) return false;
      if (!query) return true;
      return [item.name, item.legal_name, item.phone, item.email].some((value) => value?.toLowerCase().includes(query));
    });
  }, [counterparties, selectedFolderId, showArchive, search]);

  const submitFolder = async (payload: { name: string; parent_id: number | null }) => {
    if (!token || !rootFolderId) return;
    await createCounterpartyFolder(token, { ...payload, parent_id: payload.parent_id ?? rootFolderId });
    setShowFolderModal(false);
    await loadAll();
  };

  const submitCounterparty = async (payload: Partial<CounterpartyDto>, cardColor: string | null) => {
    if (!token || !rootFolderId) return;
    const safePayload = { ...payload, folder_id: payload.folder_id ?? rootFolderId };
    if (editingCounterparty) {
      await updateCounterparty(token, editingCounterparty.id, safePayload);
      persistCardColor(editingCounterparty.id, cardColor);
      setSelectedCounterpartyId(editingCounterparty.id);
    } else {
      const created = await createCounterparty(token, safePayload);
      persistCardColor(created.id, cardColor);
      setSelectedCounterpartyId(created.id);
      setSelectedFolderId(created.folder_id);
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

  const onDragEnd = async (event: DragEndEvent) => {
    if (!token || !event.over) return;
    const activeId = String(event.active.id);
    const overId = String(event.over.id);
    if (activeId === overId || !rootFolderId) return;

    const dropFolderId = overId === "root-folder-drop" ? rootFolderId : overId.startsWith("folder-") ? Number(overId.replace("folder-", "")) : null;
    if (!dropFolderId) return;

    if (activeId.startsWith("folder-")) {
      const movedFolderId = Number(activeId.replace("folder-", ""));
      if (movedFolderId === rootFolderId || movedFolderId === dropFolderId || isDescendantFolder(movedFolderId, dropFolderId)) return;
      const siblings = folders.filter((item) => item.id !== movedFolderId && item.parent_id === dropFolderId);
      await updateCounterpartyFolder(token, movedFolderId, { parent_id: dropFolderId, sort_order: siblings.length });
      await loadAll();
      return;
    }

    if (activeId.startsWith("counterparty-")) {
      const movedId = Number(activeId.replace("counterparty-", ""));
      const moved = counterparties.find((item) => item.id === movedId);
      if (!moved) return;
      const siblings = counterparties.filter((item) => item.id !== moved.id && item.folder_id === dropFolderId);
      await updateCounterparty(token, moved.id, { ...moved, folder_id: dropFolderId, sort_order: siblings.length });
      setSelectedFolderId(dropFolderId);
      setSelectedCounterpartyId(null);
      await loadAll();
    }
  };

  const toggleArchive = async () => {
    if (!token || !selectedCounterparty) return;
    if (selectedCounterparty.status === "archived" || selectedCounterparty.is_archived) await restoreCounterparty(token, selectedCounterparty.id);
    else await archiveCounterparty(token, selectedCounterparty.id);
    await loadAll();
  };

  if (!rootFolderId || !selectedFolderId) return null;

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

      <DndContext onDragEnd={(event) => void onDragEnd(event)}>
        <div style={{ display: "grid", gridTemplateColumns: "260px 340px minmax(0, 1fr) 340px", alignItems: "stretch", border: "1px solid var(--border)", borderRadius: 12, minHeight: "74vh" }}>
          <div style={columnShellStyle}>
            <div style={columnHeaderStyle}>Папки</div>
            <div style={{ minHeight: 0, overflow: "auto" }}>
              <CounterpartiesTree
                folders={folders}
                rootFolderId={rootFolderId}
                selectedFolderId={selectedFolderId}
                expandedFolders={expandedFolders}
                onToggleFolder={(folderId) => setExpandedFolders((prev) => ({ ...prev, [folderId]: !prev[folderId] }))}
                onSelectFolder={(folderId) => {
                  setSelectedFolderId(folderId);
                  setSelectedCounterpartyId(null);
                }}
              />
            </div>
          </div>

          <div style={{ ...columnShellStyle, borderLeft: "1px solid var(--border)" }}>
            <div style={columnHeaderStyle}>Контрагенты</div>
            <div style={{ minHeight: 0, overflow: "auto" }}>
              <FolderCounterpartiesList
                items={selectedFolderCounterparties}
                selectedCounterpartyId={selectedCounterpartyId}
                onSelect={(counterpartyId) => setSelectedCounterpartyId(counterpartyId)}
              />
            </div>
          </div>

          <div style={{ ...columnShellStyle, borderLeft: "1px solid var(--border)" }}>
            <div style={columnHeaderStyle}>Карточка</div>
            <div style={{ minHeight: 0, overflow: "auto" }}>
              <CounterpartyViewer
                counterparty={selectedCounterparty}
                folders={folders}
                cardColor={selectedCounterparty ? cardColors[selectedCounterparty.id] ?? null : null}
                onEdit={() => {
                  if (!selectedCounterparty) return;
                  setEditingCounterparty(selectedCounterparty);
                  setShowCounterpartyModal(true);
                }}
                onToggleArchive={() => void toggleArchive()}
              />
            </div>
          </div>

          <div style={{ ...columnShellStyle, borderLeft: "1px solid var(--border)" }}>
            <div style={columnHeaderStyle}>Автозадачи</div>
            <div style={{ minHeight: 0, overflow: "auto" }}>
              <AutoTasksPanel counterparty={selectedCounterparty} />
            </div>
          </div>
        </div>
      </DndContext>

      {showCounterpartyModal ? (
        <CreateCounterpartyModal
          folders={folders}
          rootFolderId={rootFolderId}
          initial={editingCounterparty}
          initialCardColor={editingCounterparty ? cardColors[editingCounterparty.id] ?? null : null}
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
