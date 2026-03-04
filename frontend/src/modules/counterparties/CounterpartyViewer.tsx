import { ReactNode } from "react";
import { CounterpartyDto, CounterpartyFolderDto } from "../../api/counterparties";

type CounterpartyViewerProps = {
  mode: "folder" | "counterparty";
  counterparty: CounterpartyDto | null;
  folder: CounterpartyFolderDto | null;
  folders: CounterpartyFolderDto[];
  contentFolders: CounterpartyFolderDto[];
  contentCounterparties: CounterpartyDto[];
  showArchive: boolean;
  onEdit: () => void;
  onToggleArchive: () => void;
  onSelectCounterparty: (counterpartyId: number) => void;
  onSelectFolder: (folderId: number) => void;
};

const rowStyle = { display: "grid", gridTemplateColumns: "220px 1fr", gap: 8 };

const renderValue = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") {
    return <span style={{ color: "var(--text-secondary)" }}>—</span>;
  }
  return <span>{value}</span>;
};

const ViewerSection = ({ title, children }: { title: string; children: ReactNode }) => (
  <article className="admin-card" style={{ display: "grid", gap: 10 }}>
    <h4 style={{ margin: 0 }}>{title}</h4>
    <div style={{ display: "grid", gap: 8 }}>{children}</div>
  </article>
);

const CounterpartyViewer = ({
  mode,
  counterparty,
  folder,
  folders,
  contentFolders,
  contentCounterparties,
  showArchive,
  onEdit,
  onToggleArchive,
  onSelectCounterparty,
  onSelectFolder,
}: CounterpartyViewerProps) => {
  if (mode === "folder") {
    const title = folder ? `Содержимое папки: ${folder.name}` : "Содержимое папки: Каталог";
    return (
      <section className="admin-card" style={{ display: "grid", gap: 12 }}>
        <h3 style={{ margin: 0 }}>{title}</h3>
        <div style={{ display: "grid", gap: 8 }}>
          {contentFolders.length === 0 && contentCounterparties.length === 0 ? (
            <span style={{ color: "var(--text-secondary)" }}>В этой папке пока ничего нет.</span>
          ) : null}

          {contentFolders.map((item) => (
            <button
              key={`folder-${item.id}`}
              type="button"
              className="ghost-button"
              style={{ justifyContent: "flex-start" }}
              onClick={() => onSelectFolder(item.id)}
            >
              📁 {item.name}
            </button>
          ))}

          {contentCounterparties.map((item) => (
            <button
              key={`counterparty-${item.id}`}
              type="button"
              className="ghost-button"
              style={{ justifyContent: "flex-start" }}
              onClick={() => onSelectCounterparty(item.id)}
            >
              📄 {item.name} {showArchive && (item.is_archived || item.status === "archived") ? "(архив)" : ""}
            </button>
          ))}
        </div>
      </section>
    );
  }

  if (!counterparty) {
    return <section className="admin-card">Выберите контрагента или папку в дереве слева.</section>;
  }

  const folderName = folders.find((item) => item.id === counterparty.folder_id)?.name ?? "Каталог (корень)";
  const archiveButtonTitle = counterparty.status === "archived" || counterparty.is_archived ? "Вернуть в активные" : "В архив";

  return (
    <section style={{ display: "grid", gap: 12 }}>
      <section className="admin-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>{counterparty.name}</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="ghost-button" onClick={onEdit}>Редактировать</button>
          <button type="button" className="secondary-button" onClick={onToggleArchive}>{archiveButtonTitle}</button>
        </div>
      </section>

      <ViewerSection title="Основное">
        <div style={rowStyle}><strong>Папка</strong>{renderValue(folderName)}</div>
        <div style={rowStyle}><strong>Юр. наименование</strong>{renderValue(counterparty.legal_name)}</div>
        <div style={rowStyle}><strong>Город</strong>{renderValue(counterparty.city)}</div>
        <div style={rowStyle}><strong>Товарная группа</strong>{renderValue(counterparty.product_group)}</div>
        <div style={rowStyle}><strong>Отдел</strong>{renderValue(counterparty.department)}</div>
        <div style={rowStyle}><strong>Статус</strong>{renderValue(counterparty.status)}</div>
      </ViewerSection>

      <ViewerSection title="Контакты и доступы">
        <div style={rowStyle}><strong>Телефон</strong>{renderValue(counterparty.phone)}</div>
        <div style={rowStyle}><strong>Email</strong>{renderValue(counterparty.email)}</div>
        <div style={rowStyle}><strong>Сайт</strong>{renderValue(counterparty.website)}</div>
        <div style={rowStyle}><strong>Мессенджер</strong>{renderValue(counterparty.messenger)}</div>
        <div style={rowStyle}><strong>Логин</strong>{renderValue(counterparty.login)}</div>
        <div style={rowStyle}><strong>Пароль</strong>{renderValue(counterparty.password)}</div>
      </ViewerSection>

      <ViewerSection title="Логистика">
        <div style={rowStyle}><strong>День заявки</strong>{renderValue(counterparty.order_day_of_week)}</div>
        <div style={rowStyle}><strong>Дедлайн заявки</strong>{renderValue(counterparty.order_deadline_time)}</div>
        <div style={rowStyle}><strong>День доставки</strong>{renderValue(counterparty.delivery_day_of_week)}</div>
        <div style={rowStyle}><strong>Заметки</strong>{renderValue(counterparty.defect_notes)}</div>
      </ViewerSection>

      <ViewerSection title="Автозадачи">
        <p style={{ margin: 0, color: "var(--text-secondary)" }}>
          Блок автозадач доступен в режиме просмотра. Настройка правил остается в текущем API без изменений.
        </p>
      </ViewerSection>
    </section>
  );
};

export default CounterpartyViewer;
