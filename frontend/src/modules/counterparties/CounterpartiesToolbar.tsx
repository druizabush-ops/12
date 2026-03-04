import { ChangeEvent } from "react";

type CounterpartiesToolbarProps = {
  search: string;
  showArchive: boolean;
  onSearchChange: (value: string) => void;
  onToggleArchive: () => void;
  onCreateCounterparty: () => void;
  onCreateFolder: () => void;
};

const CounterpartiesToolbar = ({
  search,
  showArchive,
  onSearchChange,
  onToggleArchive,
  onCreateCounterparty,
  onCreateFolder,
}: CounterpartiesToolbarProps) => {
  const onSearchInput = (event: ChangeEvent<HTMLInputElement>) => onSearchChange(event.target.value);

  return (
    <div className="admin-card" style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <button type="button" className="primary-button" onClick={onCreateCounterparty}>+ Контрагент</button>
      <button type="button" className="ghost-button" onClick={onCreateFolder}>+ Папка</button>
      <div style={{ position: "relative", minWidth: 320, width: "min(520px, 100%)", flex: "1 1 420px" }}>
        <span style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)" }}>🔍</span>
        <input
          placeholder="Поиск в выбранной папке: name / legal_name / phone / email"
          value={search}
          onChange={onSearchInput}
          style={{ width: "100%", fontSize: 16, padding: "11px 42px", borderRadius: 999, border: "1px solid var(--border)" }}
        />
        {search ? (
          <button
            type="button"
            className="ghost-button"
            onClick={() => onSearchChange("")}
            style={{ position: "absolute", right: 6, top: "50%", transform: "translateY(-50%)", borderRadius: 999 }}
          >
            ✕
          </button>
        ) : null}
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <input type="checkbox" checked={showArchive} onChange={onToggleArchive} />
        Показать архив
      </label>
    </div>
  );
};

export default CounterpartiesToolbar;
