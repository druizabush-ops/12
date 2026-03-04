import { CounterpartyDto } from "../../api/counterparties";

type Props = { counterparty: CounterpartyDto | null };

const AutoTasksPanel = ({ counterparty }: Props) => (
  <section className="admin-card" style={{ maxHeight: "74vh", overflow: "auto" }}>
    <h3 style={{ marginTop: 0 }}>Автозадачи</h3>
    {counterparty ? (
      <p style={{ margin: 0, color: "var(--text-secondary)" }}>Автозадачи (в разработке)</p>
    ) : (
      <p style={{ margin: 0, color: "var(--text-secondary)" }}>Выберите контрагента для просмотра панели.</p>
    )}
  </section>
);

export default AutoTasksPanel;
