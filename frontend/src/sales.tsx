import { useState, useEffect } from "react";
import {
  Users,
  CalendarDays,
  Wallet,
  ArrowRight,
  Plus,
  Download,
  BookOpen,
} from "lucide-react";
import { api, User, money, date, labelMonth } from "./api";
import categories from "./categories.json";

type Opportunity = {
  id: number;
  student: User;
  owner_id: number | null;
  owner_name: string;
  stage: string;
  cash_price: string;
  installment_count: number;
  installment_value: string;
  installment_total: string;
  selected_offer: string | null;
  contract_total: string | null;
  next_contact: string | null;
  notes: string;
  lost_reason: string;
  version: number;
  created_at: string;
  closed_at: string | null;
};
type Appointment = {
  id: number;
  opportunity_id: number;
  student_id: number;
  student_name: string;
  student_phone: string;
  owner_id: number | null;
  owner_name: string;
  starts_at: string;
  ends_at: string;
  duration_minutes: number;
  status: string;
  meeting_url: string;
  notes: string;
  version: number;
};
const stages: Record<string, string> = {
  aguardando: "Aguardando consultoria",
  agendado: "Consultoria agendada",
  consultoria: "Consultoria realizada",
  proposta: "Proposta apresentada",
  negociacao: "Em negociação",
  ganho: "Venda registrada",
  perdido: "Não convertido",
};
const appointmentStatuses: Record<string, string> = {
  agendada: "Agendada",
  confirmada: "Confirmada",
  realizada: "Realizada",
  cancelada: "Cancelada",
  nao_compareceu: "Não compareceu",
};
const stamp = (v: string) =>
  new Date(v).toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo",
    dateStyle: "short",
    timeStyle: "short",
  });
function localDate(v: string | null) {
  return v
    ? new Date(v)
        .toLocaleString("sv-SE", { timeZone: "America/Sao_Paulo" })
        .replace(" ", "T")
        .slice(0, 16)
    : "";
}
function utcDate(local: string) {
  const target = Date.parse(local + "Z");
  let instant = target;
  for (let i = 0; i < 3; i++) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Sao_Paulo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(instant));
    const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
    const wall = Date.UTC(
      Number(p.year),
      Number(p.month) - 1,
      Number(p.day),
      Number(p.hour),
      Number(p.minute),
    );
    instant += target - wall;
  }
  return new Date(instant).toISOString();
}
function body(o: Opportunity) {
  return {
    version: o.version,
    owner_id: o.owner_id,
    stage: o.stage,
    cash_price: o.cash_price,
    installment_count: o.installment_count,
    installment_value: o.installment_value,
    selected_offer: o.selected_offer,
    next_contact: o.next_contact,
    notes: o.notes,
    lost_reason: o.lost_reason,
  };
}
function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

export default function Sales({
  user,
  onDirty,
}: {
  user: User;
  onDirty: (v: boolean) => void;
}) {
  const [tab, setTab] = useState("dashboard"),
    [data, setData] = useState<any>(null),
    [owners, setOwners] = useState<{ id: number; name: string }[]>([]),
    [rev, setRev] = useState(0),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [selected, setSelected] = useState<Opportunity | null>(null),
    [booking, setBooking] = useState<{
      opportunity_id: number;
      existing?: Appointment;
    } | null>(null),
    [dirty, setDirty] = useState(false),
    [q, setQ] = useState(""),
    [stage, setStage] = useState(""),
    [ownerId, setOwner] = useState(""),
    [page, setPage] = useState(1),
    [items, setItems] = useState<any>({ items: [], total: 0 }),
    [from, setFrom] = useState(""),
    [to, setTo] = useState("");
  const mark = (v: boolean) => {
    setDirty(v);
    onDirty(v);
  };
  const guard = () =>
    !dirty ||
    confirm("Há alterações comerciais não salvas. Deseja descartá-las?");
  const navigate = (t: string) => {
    if (!guard()) return;
    mark(false);
    setSelected(null);
    setBooking(null);
    setTab(t);
    setPage(1);
    setError("");
    setMessage("");
  };
  useEffect(() => {
    let alive = true;
    api(
      "/sales/analytics?" +
        new URLSearchParams({
          ...(from ? { from_date: from } : {}),
          ...(to ? { to_date: to } : {}),
        }),
    )
      .then((r) => {
        if (alive) setData(r);
      })
      .catch((e) => setError(e.message));
    return () => {
      alive = false;
    };
  }, [rev, from, to]);
  useEffect(() => {
    api<{ id: number; name: string }[]>("/sales/owners")
      .then(setOwners)
      .catch((e) => setError(e.message));
  }, [rev]);
  useEffect(() => {
    if (!["fila", "agenda"].includes(tab)) return;
    let alive = true;
    const params = new URLSearchParams({
      page: String(page),
      ...(ownerId ? { owner_id: ownerId } : {}),
    });
    if (tab === "fila") {
      params.set("q", q);
      if (stage) params.set("stage", stage);
    } else {
      if (from) params.set("from_date", from);
      if (to) params.set("to_date", to);
    }
    api(
      "/sales/" +
        (tab === "fila" ? "opportunities" : "appointments") +
        "?" +
        params,
    )
      .then((r) => {
        if (alive) setItems(r);
      })
      .catch((e) => setError(e.message));
    return () => {
      alive = false;
    };
  }, [tab, page, q, stage, ownerId, rev, from, to]);
  async function sync() {
    if (
      !guard() ||
      !confirm(
        "Adicionar à fila comercial todos os alunos ainda não incluídos? Não serão duplicados registros existentes nem ativados acessos.",
      )
    )
      return;
    try {
      const r = await api("/sales/queue/sync", "POST", { confirm: true });
      setMessage(
        `${r.created} alunos adicionados; ${r.existing} já estavam na fila.`,
      );
      setRev((v) => v + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function open(o: Opportunity) {
    if (!guard()) return;
    try {
      setSelected(await api<Opportunity>("/sales/opportunities/" + o.id));
      setBooking(null);
      mark(false);
      setMessage("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function schedule(oid: number, existing?: Appointment) {
    if (!guard()) return;
    setSelected(null);
    setBooking({ opportunity_id: oid, existing });
    mark(false);
  }
  async function move(o: Opportunity, next: string) {
    try {
      await api("/sales/opportunities/" + o.id, "PUT", {
        ...body(o),
        stage: next,
      });
      setRev((v) => v + 1);
      setMessage("Etapa atualizada.");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <div className="heading">
        <div>
          <span className="eyebrow">MENTORIA E ACOMPANHAMENTO INDIVIDUAL</span>
          <h1>Comercial</h1>
          <p>
            Organize as consultorias e acompanhe cada conversa até a decisão do
            aluno.
          </p>
        </div>
        <button className="primary" onClick={sync}>
          <Plus size={18} /> Adicionar alunos à fila
        </button>
      </div>
      <div className="tabs" aria-label="Área comercial">
        {[
          ["dashboard", "Dashboard"],
          ["fila", "Fila de consultorias"],
          ["kanban", "Kanban"],
          ["agenda", "Agenda"],
          ["reports", "Análises e relatórios"],
        ].map(([key, label]) => (
          <button
            key={key}
            aria-pressed={tab === key}
            className={tab === key ? "selected" : ""}
            onClick={() => navigate(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      {selected && (
        <OpportunityEditor
          key={selected.id}
          opportunity={selected}
          owners={owners}
          onDirty={mark}
          onClose={() => {
            if (guard()) {
              setSelected(null);
              mark(false);
            }
          }}
          onSaved={(o) => {
            mark(false);
            setSelected(null);
            setRev((v) => v + 1);
            setMessage("Atendimento comercial salvo.");
          }}
        />
      )}
      {booking && (
        <AppointmentEditor
          key={booking.existing?.id ?? "new-" + booking.opportunity_id}
          opportunityId={booking.opportunity_id}
          existing={booking.existing}
          owners={owners}
          defaultOwner={user.id}
          onDirty={mark}
          onCancel={() => {
            if (guard()) {
              setBooking(null);
              mark(false);
            }
          }}
          onSaved={() => {
            mark(false);
            setBooking(null);
            setRev((v) => v + 1);
            setMessage("Agenda atualizada.");
          }}
        />
      )}
      {tab === "dashboard" && data && (
        <>
          <div className="sales-metrics">
            <Metric label="Alunos inscritos" value={data.students_registered} />
            <Metric
              label="Alunos com consultoria agendada"
              value={data.students_scheduled}
            />
            <Metric
              label="Aguardando consultoria"
              value={data.stages.aguardando}
            />
            <Metric
              label="Consultorias realizadas"
              value={data.appointments.realizada}
            />
            <Metric label="Vendas registradas" value={data.sales_count} />
            <Metric
              label="Valor nominal dos contratos"
              value={money(data.contract_value)}
            />
          </div>
          {data.students_without_opportunity > 0 && (
            <p className="notice">
              {data.students_without_opportunity} alunos ainda não estão no
              funil. Use “Adicionar alunos à fila” para incluí-los.
            </p>
          )}
          <section className="panel report">
            <h2>Uma consultoria que abre caminhos</h2>
            <p>
              A comunidade tem investimento de referência de{" "}
              <strong>R$ 290,00</strong>. A consultoria individual ajuda o aluno
              a organizar os primeiros passos, identificar aulas e conhecer a
              mentoria com acompanhamento individual.
            </p>
            <div className="offer-grid">
              <div>
                <h3>À vista</h3>
                <strong>R$ 5.000,00</strong>
              </div>
              <div>
                <h3>Parcelado</h3>
                <strong>12 × R$ 497,00</strong>
                <p>Total nominal: R$ 5.964,00</p>
              </div>
              <div>
                <h3>Reserva de agenda</h3>
                <strong>45 minutos</strong>
                <p>Por consultoria, ajustável ao agendar.</p>
              </div>
            </div>
            <p className="caption">
              Valores de referência, editáveis por proposta. Venda registrada
              não equivale a pagamento recebido. Não há avaliação automática de
              capacidade de pagamento.
            </p>
          </section>
          <StageChart counts={data.stages} />
        </>
      )}
      {tab === "fila" && (
        <section className="panel report">
          <h2>Fila de consultorias e vendas</h2>
          <div className="filters">
            <label className="grow">
              Buscar aluno
              <input
                type="search"
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
                  setPage(1);
                }}
                placeholder="Nome, celular ou e-mail"
              />
            </label>
            <label>
              Etapa
              <select
                value={stage}
                onChange={(e) => {
                  setStage(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todas</option>
                {Object.entries(stages).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Responsável
              <select
                value={ownerId}
                onChange={(e) => {
                  setOwner(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos</option>
                {owners.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {items.items.map((o: Opportunity) => (
            <article className="person-row" key={o.id}>
              <div className="grow">
                <strong>{o.student.name}</strong>
                <small>
                  {o.student.phone} · {o.owner_name}
                </small>
                <small>
                  {stages[o.stage]}
                  {o.next_contact
                    ? " · Próximo contato: " + stamp(o.next_contact)
                    : ""}
                </small>
              </div>
              <div className="actions">
                <button className="secondary" onClick={() => open(o)}>
                  Abrir consultoria
                </button>
                <button className="secondary" onClick={() => schedule(o.id)}>
                  Agendar reunião
                </button>
              </div>
            </article>
          ))}
          {!items.items.length && (
            <p>
              Nenhuma oportunidade nesta seleção. Adicione alunos à fila para
              começar.
            </p>
          )}
          <Pager page={page} total={items.total} size={30} onPage={setPage} />
        </section>
      )}
      {tab === "kanban" && (
        <>
          <p className="caption">
            Abra o atendimento para registrar uma proposta e a condição aceita
            antes de marcar uma venda.
          </p>
          <div className="kanban">
            {Object.entries(stages).map(([key, label]) => (
              <BoardColumn
                key={key + "-" + rev}
                stage={key}
                label={label}
                onOpen={open}
                onMove={move}
              />
            ))}
          </div>
        </>
      )}
      {tab === "agenda" && (
        <section className="panel report">
          <h2>Agenda de consultorias</h2>
          <p>
            Horários de Brasília. A duração padrão é de 45 minutos; conflitos do
            mesmo responsável são bloqueados.
          </p>
          <DateRange from={from} to={to} setFrom={setFrom} setTo={setTo} />
          <label>
            Responsável
            <select
              value={ownerId}
              onChange={(e) => {
                setOwner(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Todos</option>
              {owners.map((o) => (
                <option value={o.id} key={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          {items.items.map((a: Appointment) => (
            <article className="person-row" key={a.id}>
              <div className="grow">
                <strong>{a.student_name}</strong>
                <small>
                  {stamp(a.starts_at)} · {a.duration_minutes} minutos ·{" "}
                  {a.owner_name}
                </small>
                <small>{appointmentStatuses[a.status]}</small>
                {a.meeting_url && (
                  <a href={a.meeting_url} target="_blank" rel="noreferrer">
                    Abrir link da reunião
                  </a>
                )}
              </div>
              <button
                className="secondary"
                onClick={() => schedule(a.opportunity_id, a)}
              >
                Editar reunião
              </button>
            </article>
          ))}
          {!items.items.length && (
            <p>
              Nenhuma reunião nesta seleção. Agende pela fila de consultorias.
            </p>
          )}
          <Pager page={page} total={items.total} size={50} onPage={setPage} />
        </section>
      )}
      {tab === "reports" && data && (
        <>
          <section className="panel report">
            <div className="section-title">
              <h2>Análises comerciais</h2>
              <a className="secondary" href="/api/sales/export.csv">
                <Download size={18} /> Exportar funil completo CSV
              </a>
            </div>
            <DateRange from={from} to={to} setFrom={setFrom} setTo={setTo} />
            <p className="caption">{data.note}</p>
            <div className="sales-metrics">
              <Metric
                label="Vendas fechadas no período"
                value={data.sales_count}
              />
              <Metric
                label="Valor nominal contratado"
                value={money(data.contract_value)}
              />
              <Metric
                label="Consultorias realizadas no período"
                value={data.appointments.realizada}
              />
            </div>
            <h3>Vendas por responsável</h3>
            {data.ranking.length ? (
              data.ranking.map((x: any) => (
                <div className="person-row" key={x.owner_id ?? "none"}>
                  <strong className="grow">{x.name}</strong>
                  <span>
                    {x.sales} vendas · {money(x.contract_value)}
                  </span>
                </div>
              ))
            ) : (
              <p>Nenhuma venda registrada no período.</p>
            )}
            <h3>Resultado dos agendamentos</h3>
            {Object.entries(appointmentStatuses).map(([k, v]) => (
              <p key={k}>
                {v}: <strong>{data.appointments[k]}</strong>
              </p>
            ))}
          </section>
          <StageChart counts={data.stages} />
        </>
      )}
    </>
  );
}
function Pager({
  page,
  total,
  size,
  onPage,
}: {
  page: number;
  total: number;
  size: number;
  onPage: (p: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        {total} registros · página {page}
      </span>
      <button
        className="secondary"
        disabled={page === 1}
        onClick={() => onPage(page - 1)}
      >
        Anterior
      </button>
      <button
        className="secondary"
        disabled={page * size >= total}
        onClick={() => onPage(page + 1)}
      >
        Próxima
      </button>
    </div>
  );
}
function DateRange({
  from,
  to,
  setFrom,
  setTo,
}: {
  from: string;
  to: string;
  setFrom: (s: string) => void;
  setTo: (s: string) => void;
}) {
  return (
    <div className="form-grid">
      <label>
        Data inicial
        <input
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
      </label>
      <label>
        Data final
        <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
      </label>
    </div>
  );
}
function StageChart({ counts }: { counts: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(counts));
  return (
    <section className="panel report">
      <h2>Distribuição do funil</h2>
      {Object.entries(stages).map(([key, label]) => (
        <div className="category-bar" key={key}>
          <div>
            <span>{label}</span>
            <strong>{counts[key] ?? 0}</strong>
          </div>
          <div className="track">
            <i style={{ width: ((counts[key] ?? 0) / max) * 100 + "%" }} />
          </div>
        </div>
      ))}
    </section>
  );
}
function BoardColumn({
  stage,
  label,
  onOpen,
  onMove,
}: {
  stage: string;
  label: string;
  onOpen: (o: Opportunity) => void;
  onMove: (o: Opportunity, s: string) => Promise<void>;
}) {
  const [items, setItems] = useState<Opportunity[]>([]),
    [total, setTotal] = useState(0),
    [page, setPage] = useState(1),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api("/sales/opportunities?stage=" + stage + "&page=" + page + "&size=20")
      .then((r) => {
        if (active) {
          setItems((old) => (page === 1 ? r.items : [...old, ...r.items]));
          setTotal(r.total);
        }
      })
      .catch((e) => setError(e.message));
    return () => {
      active = false;
    };
  }, [stage, page]);
  return (
    <section className={"kanban-column stage-" + stage}>
      <h2>
        {label} <span>{total}</span>
      </h2>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {items.map((o) => (
        <BoardCard key={o.id} opportunity={o} onOpen={onOpen} onMove={onMove} />
      ))}
      {items.length < total && (
        <button className="secondary" onClick={() => setPage(page + 1)}>
          Carregar mais
        </button>
      )}
    </section>
  );
}
function BoardCard({
  opportunity: o,
  onOpen,
  onMove,
}: {
  opportunity: Opportunity;
  onOpen: (o: Opportunity) => void;
  onMove: (o: Opportunity, s: string) => Promise<void>;
}) {
  const [next, setNext] = useState(o.stage),
    [busy, setBusy] = useState(false);
  return (
    <article className="kanban-card">
      <strong>{o.student.name}</strong>
      <p>{o.owner_name}</p>
      {o.next_contact && <small>Retorno: {stamp(o.next_contact)}</small>}
      <button className="link" onClick={() => onOpen(o)}>
        Abrir atendimento <ArrowRight size={15} />
      </button>
      <label>
        Mover para
        <select value={next} onChange={(e) => setNext(e.target.value)}>
          {Object.entries(stages).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </label>
      <button
        className="secondary"
        disabled={busy || next === o.stage}
        onClick={async () => {
          setBusy(true);
          await onMove(o, next);
          setBusy(false);
        }}
      >
        Mover
      </button>
    </article>
  );
}

function OpportunityEditor({
  opportunity,
  owners,
  onDirty,
  onClose,
  onSaved,
}: {
  opportunity: Opportunity;
  owners: { id: number; name: string }[];
  onDirty: (v: boolean) => void;
  onClose: () => void;
  onSaved: (o: Opportunity) => void;
}) {
  const [form, setForm] = useState(opportunity),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [showFinancial, setShowFinancial] = useState(false);
  const set = (key: string, value: any) => {
    setForm((f) => ({ ...f, [key]: value }));
    onDirty(true);
  };
  return (
    <section className="panel report sales-editor">
      <div className="section-title">
        <h2>Consultoria · {opportunity.student.name}</h2>
        <button className="secondary" onClick={onClose}>
          Fechar atendimento
        </button>
      </div>
      <p>
        {opportunity.student.phone} ·{" "}
        {opportunity.student.email || "E-mail não informado"}
      </p>
      <p className="notice">
        Escute a realidade do aluno, organize os primeiros passos e apresente a
        mentoria quando fizer sentido para ele. Valores previstos não comprovam
        que uma contratação cabe no orçamento.
      </p>
      <button
        className="secondary"
        aria-expanded={showFinancial}
        onClick={() => setShowFinancial(!showFinancial)}
      >
        <Wallet size={18} />{" "}
        {showFinancial
          ? "Fechar visão financeira"
          : "Consultar planejamento financeiro"}
      </button>
      {showFinancial && <CommercialFinancial sid={opportunity.student.id} />}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            onSaved(
              await api<Opportunity>(
                "/sales/opportunities/" + form.id,
                "PUT",
                body(form),
              ),
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="form-grid">
          <label>
            Etapa comercial
            <select
              value={form.stage}
              onChange={(e) => set("stage", e.target.value)}
            >
              {Object.entries(stages).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Responsável
            <select
              value={form.owner_id ?? ""}
              onChange={(e) =>
                set("owner_id", e.target.value ? Number(e.target.value) : null)
              }
            >
              <option value="">Sem responsável</option>
              {owners.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Próximo contato · Brasília
            <input
              type="datetime-local"
              value={localDate(form.next_contact)}
              onChange={(e) =>
                set(
                  "next_contact",
                  e.target.value ? utcDate(e.target.value) : null,
                )
              }
            />
          </label>
          <label>
            Condição aceita
            <select
              value={form.selected_offer ?? ""}
              onChange={(e) => set("selected_offer", e.target.value || null)}
            >
              <option value="">Ainda não definida</option>
              <option value="cash">À vista</option>
              <option value="installments">Parcelado</option>
            </select>
          </label>
        </div>
        <fieldset>
          <legend>Proposta de mentoria individual</legend>
          <div className="form-grid">
            <label>
              Preço à vista (R$)
              <input
                inputMode="decimal"
                value={form.cash_price.replace(".", ",")}
                onChange={(e) =>
                  set("cash_price", e.target.value.replace(",", "."))
                }
              />
            </label>
            <label>
              Número de parcelas
              <input
                type="number"
                min={1}
                max={120}
                value={form.installment_count}
                onChange={(e) =>
                  set("installment_count", Number(e.target.value))
                }
              />
            </label>
            <label>
              Valor de cada parcela (R$)
              <input
                inputMode="decimal"
                value={form.installment_value.replace(".", ",")}
                onChange={(e) =>
                  set("installment_value", e.target.value.replace(",", "."))
                }
              />
            </label>
          </div>
          <p>
            Total parcelado:{" "}
            <strong>
              {money(Number(form.installment_value) * form.installment_count)}
            </strong>
            . Esta informação é uma proposta, não um pagamento confirmado.
          </p>
        </fieldset>
        <label>
          Atendimento, aulas indicadas e próximos passos
          <textarea
            rows={5}
            value={form.notes}
            onChange={(e) => set("notes", e.target.value)}
            maxLength={10000}
          />
          <small>
            Registro comercial interno. Orientações que o aluno deve receber são
            liberadas pela área de atendimento da consultoria.
          </small>
        </label>
        {form.stage === "perdido" && (
          <label>
            Motivo de não conversão
            <textarea
              value={form.lost_reason}
              onChange={(e) => set("lost_reason", e.target.value)}
              maxLength={2000}
            />
          </label>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy}>
          {busy ? "Salvando…" : "Salvar atendimento comercial"}
        </button>
      </form>
    </section>
  );
}
function AppointmentEditor({
  opportunityId,
  existing,
  owners,
  defaultOwner,
  onDirty,
  onCancel,
  onSaved,
}: {
  opportunityId: number;
  existing?: Appointment;
  owners: { id: number; name: string }[];
  defaultOwner: number;
  onDirty: (v: boolean) => void;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
      opportunity_id: opportunityId,
      owner_id:
        existing?.owner_id ??
        (owners.some((o) => o.id === defaultOwner)
          ? defaultOwner
          : (owners[0]?.id ?? 0)),
      starts_at: existing?.starts_at ?? "",
      duration_minutes: existing?.duration_minutes ?? 45,
      status: existing?.status ?? "agendada",
      meeting_url: existing?.meeting_url ?? "",
      notes: existing?.notes ?? "",
    }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [name, setName] = useState("");
  useEffect(() => {
    api<Opportunity>("/sales/opportunities/" + opportunityId)
      .then((o) => setName(o.student.name))
      .catch((e) => setError(e.message));
  }, [opportunityId]);
  const set = (key: string, value: any) => {
    setForm((f) => ({ ...f, [key]: value }));
    onDirty(true);
  };
  return (
    <form
      className="panel report sales-editor"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          await api(
            "/sales/appointments" + (existing ? "/" + existing.id : ""),
            existing ? "PUT" : "POST",
            { ...form, ...(existing ? { version: existing.version } : {}) },
          );
          onSaved();
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2>
        {existing ? "Editar reunião" : "Agendar consultoria"} · {name}
      </h2>
      <div className="form-grid">
        <label>
          Data e horário · Brasília
          <input
            type="datetime-local"
            value={localDate(form.starts_at)}
            onChange={(e) =>
              set("starts_at", e.target.value ? utcDate(e.target.value) : "")
            }
            required
          />
        </label>
        <label>
          Duração em minutos
          <input
            type="number"
            min={15}
            max={180}
            value={form.duration_minutes}
            onChange={(e) => set("duration_minutes", Number(e.target.value))}
            required
          />
        </label>
        <label>
          Responsável
          <select
            value={form.owner_id}
            onChange={(e) => set("owner_id", Number(e.target.value))}
            required
          >
            <option value={0}>Selecione</option>
            {owners.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Situação da reunião
          <select
            value={form.status}
            onChange={(e) => set("status", e.target.value)}
          >
            {Object.entries(appointmentStatuses).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Link da reunião · opcional
        <input
          type="url"
          value={form.meeting_url}
          onChange={(e) => set("meeting_url", e.target.value)}
          placeholder="https://..."
        />
      </label>
      <label>
        Observações da agenda
        <textarea
          value={form.notes}
          onChange={(e) => set("notes", e.target.value)}
          maxLength={10000}
        />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="actions">
        <button className="primary" disabled={busy}>
          {busy ? "Salvando…" : "Salvar reunião"}
        </button>
        <button
          className="secondary"
          type="button"
          disabled={busy}
          onClick={onCancel}
        >
          Cancelar
        </button>
      </div>
      <p className="caption">
        Agenda interna da P4. Nenhum convite externo é enviado automaticamente.
      </p>
    </form>
  );
}
function CommercialFinancial({ sid }: { sid: number }) {
  const [data, setData] = useState<any>(null),
    [error, setError] = useState(""),
    [mode, setMode] = useState("forecast"),
    [month, setMonth] = useState("");
  useEffect(() => {
    let active = true;
    api("/sales/financial/" + sid)
      .then((r) => {
        if (active) {
          setData(r);
          setMonth(r.plan?.selected_month ?? "");
        }
      })
      .catch((e) => setError(e.message));
    return () => {
      active = false;
    };
  }, [sid]);
  if (error)
    return (
      <p className="error" role="alert">
        {error}
      </p>
    );
  if (!data) return <p role="status">Carregando visão financeira…</p>;
  if (!data.plan)
    return (
      <p className="notice">
        O aluno ainda não iniciou o planejamento. Não há dados suficientes para
        avaliar uma proposta.
      </p>
    );
  const report = data[mode],
    selected = report?.months.find((m: any) => m.month === month);
  return (
    <section className="subcard financial-readonly">
      <h3>Planejamento do aluno · somente leitura</h3>
      <p className="notice">{data.notice}</p>
      {report?.incomplete && (
        <p className="notice">
          Preenchimento incompleto: totais parciais e valores desconhecidos não
          equivalem a zero.
        </p>
      )}
      <div className="form-grid">
        <label>
          Série financeira
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="forecast">Previstos</option>
            <option value="actual">Realizados</option>
          </select>
        </label>
        <label>
          Mês financeiro
          <select value={month} onChange={(e) => setMonth(e.target.value)}>
            {report?.months.map((m: any) => (
              <option key={m.month} value={m.month}>
                {labelMonth(m.month)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {selected && (
        <>
          <div className="sales-metrics">
            <Metric
              label="Entradas conhecidas"
              value={money(selected.income)}
            />
            <Metric
              label="Saídas consideradas"
              value={money(selected.outflow)}
            />
            <Metric label="Sobra ou falta" value={money(selected.balance)} />
          </div>
          <h3>Valores cadastrados no mês</h3>
          {data.plan.entries
            .filter((e: any) => e.month === month)
            .map((e: any) => (
              <p key={e.key}>
                <strong>{e.label}</strong> · {money(e[mode])}
                {e.deducted ? " · já descontado em folha" : ""}
                {e.absent ? " · marcado como não existente" : ""}
              </p>
            ))}
          <h3>Comprometimentos por categoria</h3>
          {categories
            .filter((c) => c.code !== "rendas")
            .map((c) => (
              <p key={c.code}>
                {c.label}: {money(selected.categories[c.code])} ·{" "}
                {selected.percentages[c.code] === null
                  ? "percentual indisponível"
                  : selected.percentages[c.code] + "%"}
              </p>
            ))}
        </>
      )}
      <h3>Visão dos 12 meses</h3>
      <div className="monthly">
        {report?.months.map((m: any) => (
          <article key={m.month}>
            <strong>{labelMonth(m.month)}</strong>
            <p>Entradas: {money(m.income)}</p>
            <p>Saídas: {money(m.outflow)}</p>
            <p>Sobra/falta: {money(m.balance)}</p>
          </article>
        ))}
      </div>
      <h3>Dívidas e metas informadas</h3>
      {data.plan.debts.map((d: any) => (
        <p key={d.key}>
          <strong>{d.institution}</strong> · {d.kind} · saldo {money(d.balance)}{" "}
          · parcelas {d.installments ?? "não informado"} · garantia{" "}
          {d.guaranteed ? "sim" : "não"}
        </p>
      ))}
      {data.plan.goals.map((g: any, i: number) => (
        <p key={i}>
          <strong>{g.title}</strong> · {money(g.amount)} · prazo{" "}
          {g.deadline ?? "não informado"} · {g.negotiation}
        </p>
      ))}
      <h3>Orientações liberadas pela consultoria</h3>
      {data.guidance.map((n: any, i: number) => (
        <p className="preserve" key={i}>
          {n.text}
        </p>
      ))}
    </section>
  );
}
