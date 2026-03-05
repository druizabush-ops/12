import { ReactNode } from "react";
import { CounterpartyDto, CounterpartyFolderDto } from "../../api/counterparties";

type CounterpartyViewerProps = {
  counterparty: CounterpartyDto | null;
  folders: CounterpartyFolderDto[];
  cardColor: string | null;
  onEdit: () => void;
  onToggleArchive: () => void;
};

const rowStyle = { display: "grid", gridTemplateColumns: "220px 1fr", gap: 8 };

const weekdayMap: Record<number, string> = { 1: "ПН", 2: "ВТ", 3: "СР", 4: "ЧТ", 5: "ПТ", 6: "СБ", 7: "ВС" };

const formatWeekday = (value: number | null | undefined) => (value ? weekdayMap[value] ?? String(value) : null);
const formatTime = (value: string | null | undefined) => (value ? value.slice(0, 5) : null);

const renderValue = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") return <span style={{ color: "var(--text-secondary)" }}>—</span>;
  return <span>{value}</span>;
};

const ViewerSection = ({ title, children }: { title: string; children: ReactNode }) => (
  <article className="admin-card" style={{ display: "grid", gap: 10 }}>
    <h4 style={{ margin: 0 }}>{title}</h4>
    <div style={{ display: "grid", gap: 8 }}>{children}</div>
  </article>
);

const CounterpartyViewer = ({ counterparty, folders, cardColor, onEdit, onToggleArchive }: CounterpartyViewerProps) => {
  if (!counterparty) return <section className="admin-card">Выберите контрагента в списке.</section>;

  const folderName = folders.find((item) => item.id === counterparty.folder_id)?.name ?? "Каталог";
  const archiveButtonTitle = counterparty.status === "archived" || counterparty.is_archived ? "Вернуть" : "В архив";

  return (
    <section style={{ display: "grid", gap: 12, background: cardColor || undefined, borderRadius: 12, padding: cardColor ? 8 : 0 }}>
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
        <div style={rowStyle}><strong>Статус</strong>{renderValue(counterparty.status)}</div>
      </ViewerSection>

      <ViewerSection title="Контакты и доступы">
        <div style={rowStyle}><strong>Телефон</strong>{renderValue(counterparty.phone)}</div>
        <div style={rowStyle}><strong>Email</strong>{renderValue(counterparty.email)}</div>
        <div style={rowStyle}><strong>Сайт</strong>{renderValue(counterparty.website)}</div>
        <div style={rowStyle}><strong>Мессенджер</strong>{renderValue(counterparty.messenger)}</div>
      </ViewerSection>

      <ViewerSection title="Логистика">
        <div style={rowStyle}><strong>День заявки</strong>{renderValue(formatWeekday(counterparty.order_day_of_week))}</div>
        <div style={rowStyle}><strong>Время заявки</strong>{renderValue(formatTime(counterparty.order_deadline_time))}</div>
        <div style={rowStyle}><strong>День доставки</strong>{renderValue(formatWeekday(counterparty.delivery_day_of_week))}</div>
      </ViewerSection>
    </section>
  );
};

export default CounterpartyViewer;
