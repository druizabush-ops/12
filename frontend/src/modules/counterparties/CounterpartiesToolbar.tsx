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
      <input
        placeholder="Поиск"
        value={search}
        onChange={onSearchInput}
        style={{ minWidth: 240, flex: "1 1 240px" }}
      />
      <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <input type="checkbox" checked={showArchive} onChange={onToggleArchive} />
        Показать архив
      </label>
    </div>
  );
};

export default CounterpartiesToolbar;
