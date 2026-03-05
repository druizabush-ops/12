import { FormEvent, useMemo, useState } from "react";

import { CounterpartyDto, CounterpartyFolderDto } from "../../api/counterparties";

type CreateCounterpartyModalProps = {
  folders: CounterpartyFolderDto[];
  rootFolderId: number;
  initial?: Partial<CounterpartyDto> | null;
  initialCardColor?: string | null;
  onClose: () => void;
  onSubmit: (payload: Partial<CounterpartyDto>, cardColor: string | null) => Promise<void>;
};

const weekDayOptions = [
  { value: 1, label: "ПН" },
  { value: 2, label: "ВТ" },
  { value: 3, label: "СР" },
  { value: 4, label: "ЧТ" },
  { value: 5, label: "ПТ" },
  { value: 6, label: "СБ" },
  { value: 7, label: "ВС" },
];

const CreateCounterpartyModal = ({ folders, rootFolderId, initial, initialCardColor, onClose, onSubmit }: CreateCounterpartyModalProps) => {
  const [form, setForm] = useState<Partial<CounterpartyDto>>({
    folder_id: initial?.folder_id ?? rootFolderId,
    name: initial?.name ?? "",
    legal_name: initial?.legal_name ?? "",
    city: initial?.city ?? "",
    product_group: initial?.product_group ?? "",
    department: initial?.department ?? "",
    phone: initial?.phone ?? "",
    email: initial?.email ?? "",
    website: initial?.website ?? "",
    messenger: initial?.messenger ?? "",
    login: initial?.login ?? "",
    password: initial?.password ?? "",
    order_day_of_week: initial?.order_day_of_week ?? null,
    order_deadline_time: initial?.order_deadline_time?.slice(0, 5) ?? "",
    delivery_day_of_week: initial?.delivery_day_of_week ?? null,
    defect_notes: initial?.defect_notes ?? "",
    status: initial?.status ?? "active",
  });
  const [cardColor, setCardColor] = useState<string>(initialCardColor ?? "");

  const title = useMemo(() => (initial?.id ? "Редактировать контрагента" : "Создать контрагента"), [initial?.id]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await onSubmit(
      {
        ...form,
        folder_id: form.folder_id ?? rootFolderId,
        order_deadline_time: form.order_deadline_time || null,
        order_day_of_week: form.order_day_of_week || null,
        delivery_day_of_week: form.delivery_day_of_week || null,
      },
      cardColor || null,
    );
  };

  return (
    <div className="admin-modal-backdrop">
      <form className="admin-modal" onSubmit={(event) => void submit(event)} style={{ width: 680, maxWidth: "95vw" }}>
        <h3>{title}</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(200px, 1fr))", gap: 8 }}>
          <select value={form.folder_id ?? rootFolderId} onChange={(e) => setForm((prev) => ({ ...prev, folder_id: e.target.value ? Number(e.target.value) : rootFolderId }))}>
            <option value={rootFolderId}>Каталог (корень)</option>
            {folders.filter((folder) => folder.id !== rootFolderId).map((folder) => <option key={folder.id} value={folder.id}>{folder.name}</option>)}
          </select>
          <input type="color" title="Цвет карточки" value={cardColor || "#ffffff"} onChange={(e) => setCardColor(e.target.value)} />
          <input placeholder="Наименование" value={form.name ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} required />
          <input placeholder="Юр. наименование" value={form.legal_name ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, legal_name: e.target.value }))} />
          <input placeholder="Город" value={form.city ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value }))} />
          <input placeholder="Телефон" value={form.phone ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))} />
          <input placeholder="Email" value={form.email ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))} />
          <input placeholder="Сайт" value={form.website ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, website: e.target.value }))} />
          <input placeholder="Мессенджер" value={form.messenger ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, messenger: e.target.value }))} />
          <select value={form.order_day_of_week ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, order_day_of_week: e.target.value ? Number(e.target.value) : null }))}>
            <option value="">День заявки</option>
            {weekDayOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
          <div style={{ display: "flex", gap: 8 }}>
            <input type="time" value={form.order_deadline_time ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, order_deadline_time: e.target.value }))} style={{ flex: 1 }} />
            <button type="button" className="ghost-button" onClick={() => setForm((prev) => ({ ...prev, order_deadline_time: "" }))}>Очистить</button>
          </div>
          <select value={form.delivery_day_of_week ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, delivery_day_of_week: e.target.value ? Number(e.target.value) : null }))}>
            <option value="">День доставки</option>
            {weekDayOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </div>
        <div className="admin-modal-actions">
          <button type="submit" className="primary-button">Сохранить</button>
          <button type="button" className="ghost-button" onClick={() => setCardColor("")}>Сбросить цвет</button>
          <button type="button" className="ghost-button" onClick={onClose}>Отмена</button>
        </div>
      </form>
    </div>
  );
};

export default CreateCounterpartyModal;
