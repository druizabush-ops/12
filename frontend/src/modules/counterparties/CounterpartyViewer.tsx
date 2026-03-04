import { CounterpartyDto, CounterpartyFolderDto } from "../../api/counterparties";

type CounterpartyViewerProps = {
  counterparty: CounterpartyDto | null;
  folders: CounterpartyFolderDto[];
  onEdit: () => void;
};

const rowStyle = { display: "grid", gridTemplateColumns: "180px 1fr", gap: 8 };

const CounterpartyViewer = ({ counterparty, folders, onEdit }: CounterpartyViewerProps) => {
  if (!counterparty) {
    return <section className="admin-card">Выберите контрагента в дереве слева.</section>;
  }

  const folderName = folders.find((item) => item.id === counterparty.folder_id)?.name ?? "—";

  return (
    <section className="admin-card" style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>{counterparty.name}</h3>
        <button type="button" className="ghost-button" onClick={onEdit}>Редактировать</button>
      </div>
      <div style={rowStyle}><strong>Папка</strong><span>{folderName}</span></div>
      <div style={rowStyle}><strong>Юр. наименование</strong><span>{counterparty.legal_name ?? "—"}</span></div>
      <div style={rowStyle}><strong>Город</strong><span>{counterparty.city ?? "—"}</span></div>
      <div style={rowStyle}><strong>Товарная группа</strong><span>{counterparty.product_group ?? "—"}</span></div>
      <div style={rowStyle}><strong>Отдел</strong><span>{counterparty.department ?? "—"}</span></div>
      <div style={rowStyle}><strong>Телефон</strong><span>{counterparty.phone ?? "—"}</span></div>
      <div style={rowStyle}><strong>Email</strong><span>{counterparty.email ?? "—"}</span></div>
      <div style={rowStyle}><strong>Сайт</strong><span>{counterparty.website ?? "—"}</span></div>
      <div style={rowStyle}><strong>Мессенджер</strong><span>{counterparty.messenger ?? "—"}</span></div>
      <div style={rowStyle}><strong>Логин</strong><span>{counterparty.login ?? "—"}</span></div>
      <div style={rowStyle}><strong>Пароль</strong><span>{counterparty.password ?? "—"}</span></div>
      <div style={rowStyle}><strong>День заявки</strong><span>{counterparty.order_day_of_week ?? "—"}</span></div>
      <div style={rowStyle}><strong>Дедлайн заявки</strong><span>{counterparty.order_deadline_time ?? "—"}</span></div>
      <div style={rowStyle}><strong>День доставки</strong><span>{counterparty.delivery_day_of_week ?? "—"}</span></div>
      <div style={rowStyle}><strong>Заметки</strong><span>{counterparty.defect_notes ?? "—"}</span></div>
      <div style={rowStyle}><strong>Статус</strong><span>{counterparty.status}</span></div>
    </section>
  );
};

export default CounterpartyViewer;
