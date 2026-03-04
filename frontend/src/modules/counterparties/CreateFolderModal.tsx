import { FormEvent, useState } from "react";

import { CounterpartyFolderDto } from "../../api/counterparties";

type CreateFolderModalProps = {
  folders: CounterpartyFolderDto[];
  onClose: () => void;
  onSubmit: (payload: { name: string; parent_id: number | null }) => Promise<void>;
};

const CreateFolderModal = ({ folders, onClose, onSubmit }: CreateFolderModalProps) => {
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState<number | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    await onSubmit({ name: name.trim(), parent_id: parentId });
  };

  return (
    <div className="admin-modal-backdrop">
      <form className="admin-modal" onSubmit={(event) => void submit(event)}>
        <h3>Создать папку</h3>
        <input placeholder="Название папки" value={name} onChange={(event) => setName(event.target.value)} required />
        <select value={parentId ?? ""} onChange={(event) => setParentId(event.target.value ? Number(event.target.value) : null)}>
          <option value="">Корень</option>
          {folders.map((folder) => <option key={folder.id} value={folder.id}>{folder.name}</option>)}
        </select>
        <div className="admin-modal-actions">
          <button type="submit" className="primary-button">Сохранить</button>
          <button type="button" className="ghost-button" onClick={onClose}>Отмена</button>
        </div>
      </form>
    </div>
  );
};

export default CreateFolderModal;
