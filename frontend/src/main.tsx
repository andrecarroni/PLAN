import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  Wallet,
  ChartNoAxesCombined,
  BookOpen,
  UserRound,
  Users,
  Settings,
  LogOut,
  Menu,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  Plus,
  Trash2,
  Check,
  CheckCircle2,
  Clock,
  ShieldCheck,
  HeartHandshake,
  Download,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  api,
  ApiError,
  setCsrf,
  User,
  Plan,
  Entry,
  Debt,
  Goal,
  money,
  date,
  labelMonth,
  months,
} from "./api";
import categories from "./categories.json";
import "./style.css";
const steps = [
  ...categories.map((c) => c.label),
  "Metas e negociação",
  "Revisão dos dados",
];
const tips = [
  "Informe a renda líquida que você recebe na conta. Inclua outras rendas no mês previsto.",
  "Registre pagamentos mensais das dívidas sem garantia. O saldo devedor é uma informação separada.",
  "Indique se o consignado já foi descontado da renda líquida. Assim evitamos subtrair duas vezes.",
  "Inclua aluguel, financiamentos com garantia e despesas que têm valores estáveis.",
  "Registre gastos que variam, como mercado, água e energia.",
  "Registre despesas eventuais no mês em que pretende pagá-las.",
  "Defina seus objetivos e prazos. Uma previsão não é garantia de resultado.",
  "Confira o período e os dados. Valores desconhecidos ficam em branco, sem virar zero.",
];
function Brand() {
  const [logo, setLogo] = useState(true);
  return (
    <div className="brand">
      {logo ? (
        <img
          src="/logo.png"
          alt="P4 Consultoria Financeira"
          onError={() => setLogo(false)}
        />
      ) : (
        <>
          <strong>
            P4 <span>CONSULTORES</span>
          </strong>
          <small>PLANEJAMENTO FINANCEIRO</small>
        </>
      )}
    </div>
  );
}
function Heading({
  title,
  children,
  action,
}: {
  title: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="heading">
      <div>
        <span className="eyebrow">P4 CONSULTORES · UM PASSO DE CADA VEZ</span>
        <h1>{title}</h1>
        {children && <p>{children}</p>}
      </div>
      {action}
    </div>
  );
}
function App() {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [page, setPage] = useState("plan"),
    [student, setStudent] = useState<User | null>(null),
    [nav, setNav] = useState(false),
    [large, setLarge] = useState(false),
    [dirty, setDirty] = useState(false);
  useEffect(() => {
    api("/auth/me")
      .then((r) => {
        setUser(r.user);
        setCsrf(r.csrf);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    const fn = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", fn);
    return () => window.removeEventListener("beforeunload", fn);
  }, [dirty]);
  const go = (p: string) => {
    if (
      dirty &&
      !confirm(
        "Há alterações ainda não confirmadas pelo servidor. Sair pode perdê-las. Deseja continuar?",
      )
    )
      return;
    setDirty(false);
    setPage(p);
    setNav(false);
  };
  if (loading) return <p className="loading">Carregando sua área segura…</p>;
  if (!user)
    return (
      <Login
        onLogin={(u) => {
          setUser(u);
          setPage("plan");
        }}
      />
    );
  const staff = user.roles.some((r) =>
      ["consultor", "administrador", "vendedor"].includes(r),
    ),
    finance = user.roles.some((r) =>
      ["consultor", "administrador"].includes(r),
    ),
    admin = user.roles.includes("administrador"),
    isStudent = user.roles.includes("aluno"),
    sid = student?.id ?? user.id,
    allowed = (student && finance) || (isStudent && user.status === "ativo");
  return (
    <div className={large ? "app large" : "app"}>
      <a className="skip" href="#main">
        Pular para o conteúdo
      </a>
      <aside className={"sidebar " + (nav ? "open" : "")}>
        <Brand />
        <div className="nav-label">SEU ESPAÇO FINANCEIRO</div>
        <nav aria-label="Menu principal">
          {(isStudent || student) && (
            <>
              <button
                className={page === "plan" ? "active" : ""}
                onClick={() => go("plan")}
              >
                <Wallet /> Meu planejamento
              </button>
              <button
                className={page === "report" ? "active" : ""}
                onClick={() => go("report")}
              >
                <ChartNoAxesCombined /> Meu relatório
              </button>
            </>
          )}
          <button
            className={page === "guides" ? "active" : ""}
            onClick={() => go("guides")}
          >
            <BookOpen /> Orientações
          </button>
          <button
            className={page === "account" ? "active" : ""}
            onClick={() => go("account")}
          >
            <UserRound /> Minha conta e ajuda
          </button>
          {staff && (
            <button
              className={page === "team" ? "active" : ""}
              onClick={() => go("team")}
            >
              <Users /> Alunos e atendimentos
            </button>
          )}
          {admin && (
            <button
              className={page === "admin" ? "active" : ""}
              onClick={() => go("admin")}
            >
              <Settings /> Administração
            </button>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="support-box">
            <HeartHandshake />
            <strong>Você não está sozinho.</strong>
            <p>Nossa equipe está aqui para ajudar, no seu ritmo.</p>
            <button className="link" onClick={() => go("account")}>
              Preciso de ajuda <ChevronRight size={16} />
            </button>
          </div>
          <small>
            <ShieldCheck size={15} /> Seus dados em um espaço seguro
          </small>
        </div>
      </aside>
      <div className="shell">
        <header>
          <button
            className="mobile-menu icon"
            aria-label="Abrir menu"
            onClick={() => setNav(!nav)}
          >
            <Menu />
          </button>
          <span className="breadcrumb">
            Minha área <ChevronRight size={14} />{" "}
            {page === "plan"
              ? "Meu planejamento"
              : page === "report"
                ? "Meu relatório"
                : page === "admin"
                  ? "Administração"
                  : page === "team"
                    ? "Alunos"
                    : page === "guides"
                      ? "Orientações"
                      : "Minha conta"}
          </span>
          <div className="header-actions">
            <button
              className="font-button"
              aria-label="Ampliar letras"
              aria-pressed={large}
              onClick={() => setLarge(!large)}
            >
              A+
            </button>
            <span className="avatar">{user.name[0]}</span>
            <span className="user-label">
              {user.name.split(" ")[0]}
              <small>{user.roles.join(" · ")}</small>
            </span>
            <button
              className="icon"
              aria-label="Sair da conta"
              onClick={async () => {
                if (dirty && !confirm("Sair com alterações não salvas?"))
                  return;
                try {
                  await api("/auth/logout", "POST");
                  setUser(null);
                  setDirty(false);
                } catch (e) {
                  alert((e as Error).message);
                }
              }}
            >
              <LogOut size={19} />
            </button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {student && (
            <div className="notice">
              Atendimento: <strong>{student.name}</strong>
              <button
                className="link"
                onClick={() => {
                  if (dirty && !confirm("Sair com alterações não salvas?"))
                    return;
                  setDirty(false);
                  setStudent(null);
                  setPage("team");
                }}
              >
                Voltar aos alunos
              </button>
            </div>
          )}
          {page === "plan" &&
            (allowed ? (
              <Planner
                key={sid}
                sid={sid}
                onDirty={setDirty}
                onReport={() => go("report")}
              />
            ) : (
              <section className="panel empty">
                <ShieldCheck size={36} />
                <h1>
                  {staff
                    ? "Acompanhe seus alunos"
                    : `Seu acesso está ${user.status}`}
                </h1>
                <p>
                  {staff
                    ? "Selecione um aluno na área da equipe para iniciar o atendimento."
                    : "Seus dados estão preservados. Consulte sua conta para falar com a equipe ou solicitar renovação."}
                </p>
                <button
                  className="primary"
                  onClick={() => go(staff ? "team" : "account")}
                >
                  {staff ? "Ver alunos" : "Minha conta e ajuda"}{" "}
                  <ArrowRight size={18} />
                </button>
              </section>
            ))}
          {page === "report" &&
            (allowed ? (
              <Reports key={sid} sid={sid} />
            ) : (
              <p className="notice">
                Consulte sua conta para verificar o acesso financeiro.
              </p>
            ))}
          {page === "guides" && <Guides />}
          {page === "account" && (
            <Account user={user} onLogout={() => setUser(null)} />
          )}
          {page === "team" && staff && (
            <Team
              user={user}
              onOpen={(s) => {
                setStudent(s);
                setPage("plan");
              }}
            />
          )}
          {page === "admin" && admin && <Admin />}
        </main>
        <footer>
          <span>© {new Date().getFullYear()} P4 Consultores</span>
          <span>Planejar hoje. Viver melhor amanhã.</span>
        </footer>
      </div>
    </div>
  );
}
function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [phone, setPhone] = useState(""),
    [password, setPassword] = useState(""),
    [show, setShow] = useState(false),
    [reset, setReset] = useState(false),
    [token, setToken] = useState(""),
    [message, setMessage] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <div className="login">
      <section className="login-story">
        <Brand />
        <div>
          <span className="eyebrow">CLAREZA PARA SUAS ESCOLHAS</span>
          <h1>
            O próximo passo
            <br />é seu.
            <br />
            <em>Vamos juntos.</em>
          </h1>
          <p>
            Mais organização para o seu dinheiro.
            <br />
            Mais tranquilidade para sua vida.
          </p>
        </div>
        <small>
          <ShieldCheck size={18} /> Planejamento com cuidado e confiança.
        </small>
      </section>
      <section className="login-form">
        <span className="eyebrow">BEM-VINDO À SUA ÁREA</span>
        <h2>{reset ? "Recupere seu acesso" : "Que bom ter você aqui."}</h2>
        <p>Cuide do seu planejamento, um passo de cada vez.</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              if (reset) {
                await api("/auth/reset", "POST", { token, password });
                setReset(false);
                setPassword("");
                setMessage("Senha atualizada. Entre com a nova senha.");
              } else {
                const r = await api("/auth/login", "POST", { phone, password });
                setCsrf(r.csrf);
                onLogin(r.user);
              }
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {reset ? (
            <label>
              Código temporário
              <input
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
                autoComplete="one-time-code"
              />
            </label>
          ) : (
            <label>
              Celular com DDD
              <input
                type="tel"
                autoComplete="username"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(11) 99999-9999"
                required
              />
              <small>
                Brasil: +55 automático. Para outro país, digite + e o código.
              </small>
            </label>
          )}
          <label>
            {reset ? "Nova senha" : "Senha"}
            <div className="password">
              <input
                type={show ? "text" : "password"}
                autoComplete={reset ? "new-password" : "current-password"}
                value={password}
                minLength={reset ? 6 : undefined}
                maxLength={200}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="icon"
                aria-label={show ? "Ocultar senha" : "Mostrar senha"}
                onClick={() => setShow(!show)}
              >
                {show ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>
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
          <button className="primary full" disabled={busy}>
            {busy
              ? "Aguarde…"
              : reset
                ? "Atualizar senha"
                : "Entrar na minha conta"}
            <ArrowRight size={18} />
          </button>
        </form>
        <button
          className="link"
          onClick={async () => {
            setReset(!reset);
            setError("");
            try {
              const [r, s] = await Promise.all([
                api("/auth/recover", "POST"),
                api("/support"),
              ]);
              setMessage(r.message + " " + s.contact);
            } catch (e) {
              setError((e as Error).message);
            }
          }}
        >
          {reset ? "Voltar para entrar" : "Esqueci minha senha"}
        </button>
        <p className="login-foot">
          Suas informações são pessoais e protegidas.
        </p>
      </section>
    </div>
  );
}
function Money({
  label,
  value,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string | null;
  onChange: (v: string | null) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState(value?.replace(".", ",") ?? "");
  useEffect(() => setText(value?.replace(".", ",") ?? ""), [value]);
  return (
    <label>
      {label}
      <div className="money">
        <span aria-hidden="true">R$</span>
        <input
          inputMode="decimal"
          value={text}
          placeholder="Não sei ainda"
          disabled={disabled}
          onChange={(e) => {
            const v = e.target.value;
            setText(v);
            onChange(v === "" ? null : v.replace(",", ".").replace(/\.$/, ""));
          }}
        />
      </div>
      {text && !/^\d+(,\d{0,2})?$/.test(text) && (
        <small className="error-text">
          Use números e vírgula, até duas casas.
        </small>
      )}
    </label>
  );
}
function Planner({
  sid,
  onDirty,
  onReport,
}: {
  sid: number;
  onDirty: (v: boolean) => void;
  onReport: () => void;
}) {
  const [plan, setPlan] = useState<Plan | null>(null),
    [error, setError] = useState(""),
    [status, setStatus] = useState("Dados carregados"),
    [newLabel, setNewLabel] = useState(""),
    [mode, setMode] = useState<"forecast" | "actual">("forecast"),
    [scope, setScope] = useState("one"),
    [from, setFrom] = useState(""),
    [until, setUntil] = useState(""),
    [summary, setSummary] = useState<any>(null),
    [content, setContent] = useState<any[]>([]);
  const ref = useRef<Plan | null>(null),
    dirty = useRef(false),
    revision = useRef(0),
    saving = useRef(false),
    conflict = useRef(false),
    mounted = useRef(false),
    timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => {
    mounted.current = true;
    api<Plan>("/plans/" + sid)
      .then((p) => {
        if (!mounted.current) return;
        ref.current = p;
        setPlan(p);
        setFrom(p.start);
        setUntil(months(p.start)[11]);
      })
      .catch((e) => setError(e.message));
    api("/reports/" + sid)
      .then(setSummary)
      .catch(() => {});
    api<any[]>("/contents")
      .then(setContent)
      .catch(() => {});
    return () => {
      mounted.current = false;
      clearTimeout(timer.current);
    };
  }, [sid]);
  async function save() {
    if (saving.current || !dirty.current || !ref.current || conflict.current)
      return;
    saving.current = true;
    setStatus("Salvando…");
    const sent = ref.current,
      rev = revision.current;
    try {
      const { id, user_id, ...body } = sent;
      const updated = await api<Plan>("/plans/" + sid, "PUT", body);
      if (!mounted.current) return;
      if (rev === revision.current) {
        ref.current = updated;
        setPlan(updated);
        dirty.current = false;
        onDirty(false);
        setError("");
        setStatus("Salvo");
        api("/reports/" + sid)
          .then(setSummary)
          .catch(() => {});
      } else {
        ref.current = { ...ref.current!, version: updated.version };
        setPlan(ref.current);
        setStatus("Alterações a salvar…");
      }
    } catch (e) {
      if (mounted.current) {
        setStatus("Não foi possível salvar. Tentar novamente.");
        setError((e as Error).message);
        if (e instanceof ApiError && e.status === 409) conflict.current = true;
      }
    } finally {
      saving.current = false;
      if (
        mounted.current &&
        dirty.current &&
        !conflict.current &&
        rev !== revision.current
      )
        timer.current = setTimeout(() => void save(), 700);
    }
  }
  function change(fn: (p: Plan) => Plan) {
    ref.current = fn(ref.current!);
    setPlan(ref.current);
    revision.current++;
    dirty.current = true;
    onDirty(true);
    setStatus("Alterações a salvar…");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => void save(), 800);
  }
  if (!plan)
    return (
      <>
        <Heading title="Preparando seu planejamento…" />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </>
    );
  const step = plan.step,
    cat = categories[step]?.code,
    month = plan.selected_month,
    periods = months(plan.start),
    entries = plan.entries.filter(
      (e) => e.category === cat && e.month === month,
    ),
    stats = summary?.months.find((r: any) => r.month === month);
  const edit = (entry: Entry, k: keyof Entry, v: any) =>
    change((p) => ({
      ...p,
      entries: p.entries.map((e) =>
        e.key === entry.key &&
        (scope === "next" ? e.month >= month : e.month === month)
          ? {
              ...e,
              [k]: v,
              ...(k === "absent" && v ? { forecast: null, actual: null } : {}),
            }
          : e,
      ),
    }));
  const add = () => {
    if (!newLabel.trim()) return;
    change((p) => ({
      ...p,
      entries: [
        ...p.entries,
        {
          key: crypto.randomUUID(),
          category: cat,
          label: newLabel.trim(),
          month,
          forecast: null,
          actual: null,
          deducted: cat === "consignados",
          method: "outro",
          absent: false,
        },
      ],
    }));
    setNewLabel("");
  };
  const replicate = (sourceMonth: string, targets: string[]) => {
    const source = plan.entries.filter(
      (e) => e.category === cat && e.month === sourceMonth,
    );
    if (!source.length) return setError("Não há itens no mês de origem.");
    if (
      !confirm(
        "Copiar os valores previstos para os meses selecionados? Os previstos desses mesmos itens serão substituídos; valores realizados existentes serão preservados.",
      )
    )
      return;
    change((p) => {
      const ids = new Set(source.map((e) => e.key));
      return {
        ...p,
        entries: [
          ...p.entries.filter(
            (e) => !(ids.has(e.key) && targets.includes(e.month)),
          ),
          ...targets.flatMap((m) =>
            source.map((e) => ({
              ...e,
              month: m,
              actual:
                p.entries.find((x) => x.key === e.key && x.month === m)
                  ?.actual ?? null,
            })),
          ),
        ],
      };
    });
  };
  return (
    <>
      <Heading title="Meu planejamento financeiro">
        Organize suas finanças e construa um caminho com mais tranquilidade.
      </Heading>
      <div className="welcome">
        <Wallet size={27} />
        <div>
          <strong>Seu futuro começa com um pouco de organização.</strong>
          <p>
            Não precisa preencher tudo hoje. Você pode continuar de onde parou.
          </p>
        </div>
        <span aria-hidden="true"></span>
      </div>
      <div className="stats">
        <Stat title="Entradas previstas" value={stats?.income} />
        <Stat title="Saídas previstas" value={stats?.outflow} />
        <Stat title="Sobra ou falta prevista" value={stats?.balance} dark />
      </div>
      <p className="caption">
        {labelMonth(month)} · Valores conhecidos; o resultado é parcial enquanto
        houver pendências.
      </p>
      <div className="planning">
        <section className="panel path">
          <div className="section-title">
            <h2>Seu caminho</h2>
            <span>{plan.completed.length} de 8</span>
          </div>
          <progress
            max={8}
            value={plan.completed.length}
            aria-label="Progresso de preenchimento"
          />
          <small>Progresso de preenchimento</small>
          <ol>
            {steps.map((s, i) => (
              <li key={s}>
                <button
                  className={i === step ? "current" : ""}
                  onClick={() => change((p) => ({ ...p, step: i }))}
                >
                  <span className="step-no">
                    {plan.completed.includes(i) ? <Check size={16} /> : i + 1}
                  </span>
                  <span>{s}</span>
                  {i === step && <ChevronRight size={16} />}
                </button>
              </li>
            ))}
          </ol>
          <p className="caption">
            <ShieldCheck size={16} /> Este progresso não é uma nota ou avaliação
            financeira.
          </p>
        </section>
        <div>
          <section className="panel editor">
            <div className="editor-top">
              <span className="eyebrow">ETAPA {step + 1} DE 8</span>
              <span className="save" role="status">
                {status === "Salvo" ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Clock size={16} />
                )}{" "}
                {status}
              </span>
            </div>
            <h2>{steps[step]}</h2>
            <p>{tips[step]}</p>
            {error && (
              <div className="error" role="alert">
                {error}
                {conflict.current ? (
                  <button
                    className="secondary"
                    onClick={() => {
                      if (
                        confirm(
                          "Recarregar descartará apenas suas alterações locais não salvas. Continuar?",
                        )
                      ) {
                        dirty.current = false;
                        onDirty(false);
                        window.location.reload();
                      }
                    }}
                  >
                    Recarregar dados do servidor
                  </button>
                ) : (
                  <button className="secondary" onClick={() => void save()}>
                    Tentar novamente
                  </button>
                )}
              </div>
            )}
            {step < 6 && (
              <>
                <div className="form-grid">
                  <label>
                    Mês do planejamento
                    <select
                      value={month}
                      onChange={(e) =>
                        change((p) => ({
                          ...p,
                          selected_month: e.target.value,
                        }))
                      }
                    >
                      {periods.map((m) => (
                        <option value={m} key={m}>
                          {labelMonth(m)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Valores
                    <select
                      value={mode}
                      onChange={(e) => setMode(e.target.value as any)}
                    >
                      <option value="forecast">Previstos</option>
                      <option value="actual">Realizados</option>
                    </select>
                  </label>
                </div>
                <fieldset className="scope">
                  <legend>Aplicar alteração</legend>
                  <label>
                    <input
                      type="radio"
                      name="scope"
                      checked={scope === "one"}
                      onChange={() => setScope("one")}
                    />{" "}
                    Somente neste mês
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="scope"
                      checked={scope === "next"}
                      onChange={() => setScope("next")}
                    />{" "}
                    Este e os meses seguintes já cadastrados
                  </label>
                </fieldset>
                {!entries.length && (
                  <div className="empty-item">
                    <Wallet />
                    <strong>Vamos começar por aqui?</strong>
                    <p>Adicione um item. Você pode informar o valor depois.</p>
                  </div>
                )}
                {entries.map((e) => (
                  <div className="entry" key={e.key}>
                    <div className="entry-row">
                      <label>
                        Descrição
                        <input
                          value={e.label}
                          onChange={(v) => edit(e, "label", v.target.value)}
                          maxLength={160}
                        />
                      </label>
                      <Money
                        label={
                          mode === "forecast"
                            ? "Valor previsto"
                            : "Valor realizado"
                        }
                        value={e[mode]}
                        disabled={e.absent}
                        onChange={(v) => edit(e, mode, v)}
                      />
                      <button
                        className="icon danger"
                        aria-label={"Excluir " + e.label}
                        onClick={() => {
                          if (
                            confirm(
                              "Excluir este item no intervalo de edição selecionado?",
                            )
                          )
                            change((p) => ({
                              ...p,
                              entries: p.entries.filter(
                                (x) =>
                                  !(
                                    x.key === e.key &&
                                    (scope === "next"
                                      ? x.month >= month
                                      : x.month === month)
                                  ),
                              ),
                            }));
                        }}
                      >
                        <Trash2 size={19} />
                      </button>
                    </div>
                    <div className="entry-options">
                      {cat !== "rendas" && (
                        <label>
                          <input
                            type="checkbox"
                            checked={e.absent}
                            onChange={(v) =>
                              edit(e, "absent", v.target.checked)
                            }
                          />{" "}
                          Não tenho essa despesa
                        </label>
                      )}
                      {cat === "consignados" && (
                        <label>
                          <input
                            type="checkbox"
                            checked={e.deducted}
                            onChange={(v) =>
                              edit(e, "deducted", v.target.checked)
                            }
                          />{" "}
                          Já descontado da renda líquida
                        </label>
                      )}
                      {cat !== "rendas" && cat !== "consignados" && (
                        <label>
                          Registro
                          <select
                            value={e.method}
                            onChange={(v) => edit(e, "method", v.target.value)}
                          >
                            <option value="outro">
                              Pagamento fora do cartão
                            </option>
                            <option value="cartao">
                              Compra no cartão por categoria
                            </option>
                            <option value="fatura">
                              Fatura integral do cartão
                            </option>
                          </select>
                        </label>
                      )}
                    </div>
                    {e[mode] === null && !e.absent && (
                      <small className="pending">
                        Valor pendente · pode preencher depois
                      </small>
                    )}
                  </div>
                ))}
                <div className="add-row">
                  <label className="grow">
                    Novo item
                    <input
                      list="suggestions"
                      value={newLabel}
                      maxLength={160}
                      onChange={(e) => setNewLabel(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          add();
                        }
                      }}
                      placeholder="Escolha uma sugestão ou escreva outro item"
                    />
                  </label>
                  <datalist id="suggestions">
                    {categories[step]?.suggestions.map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                  <button
                    className="secondary"
                    disabled={!newLabel.trim()}
                    onClick={add}
                  >
                    <Plus size={17} /> Adicionar item
                  </button>
                </div>
                <details>
                  <summary>Repetir ou copiar valores</summary>
                  <p>
                    Repete os valores previstos; não confirma pagamentos
                    realizados.
                  </p>
                  <div className="form-grid">
                    <label>
                      Do mês
                      <select
                        value={from}
                        onChange={(e) => setFrom(e.target.value)}
                      >
                        {periods.map((m) => (
                          <option key={m}>{m}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Até o mês
                      <select
                        value={until}
                        onChange={(e) => setUntil(e.target.value)}
                      >
                        {periods.map((m) => (
                          <option key={m}>{m}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="actions">
                    <button
                      className="secondary"
                      onClick={() =>
                        from > until
                          ? setError("O início deve ser anterior ao término.")
                          : replicate(
                              month,
                              periods.filter((m) => m >= from && m <= until),
                            )
                      }
                    >
                      Repetir no intervalo
                    </button>
                    <button
                      className="secondary"
                      disabled={month === periods[0]}
                      onClick={() =>
                        replicate(periods[periods.indexOf(month) - 1], [month])
                      }
                    >
                      Copiar mês anterior
                    </button>
                  </div>
                </details>
                {["bancarias", "consignados"].includes(cat) && (
                  <DebtFields
                    debts={plan.debts}
                    onChange={(v) => change((p) => ({ ...p, debts: v }))}
                  />
                )}
              </>
            )}
            {step === 6 && (
              <GoalFields
                goals={plan.goals}
                onChange={(v) => change((p) => ({ ...p, goals: v }))}
              />
            )}
            {step === 7 && (
              <>
                <label>
                  Primeiro mês do período
                  <input
                    type="month"
                    value={plan.start}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (!v) return;
                      if (
                        plan.entries.length &&
                        !confirm(
                          "Alterar o período remove lançamentos fora dos novos 12 meses. Continuar?",
                        )
                      )
                        return;
                      const ms = months(v);
                      change((p) => ({
                        ...p,
                        start: v,
                        selected_month: v,
                        entries: p.entries.filter((e) => ms.includes(e.month)),
                      }));
                      setFrom(v);
                      setUntil(ms[11]);
                    }}
                  />
                </label>
                <label>
                  Como registrar o cartão
                  <select
                    value={plan.card_mode}
                    onChange={(e) =>
                      change((p) => ({ ...p, card_mode: e.target.value }))
                    }
                  >
                    <option value="categorias">
                      Por categoria: excluir faturas integrais
                    </option>
                    <option value="fatura">
                      Pela fatura: excluir compras por categoria no cartão
                    </option>
                  </select>
                </label>
                <p className="notice">
                  O modo escolhido exclui o outro tipo das saídas para evitar
                  duplicidade. Não registre a mesma compra também como pagamento
                  fora do cartão.
                </p>
                <h3>Revise suas etapas</h3>
                {steps.slice(0, 7).map((s, i) => (
                  <button
                    className="review-row"
                    key={s}
                    onClick={() => change((p) => ({ ...p, step: i }))}
                  >
                    <span>{s}</span>
                    <span>
                      {plan.completed.includes(i) ? "Revisada" : "Revisar"}{" "}
                      <ChevronRight size={16} />
                    </span>
                  </button>
                ))}
                <p>
                  {
                    plan.entries.filter((e) => e.forecast === null && !e.absent)
                      .length
                  }{" "}
                  valores previstos ainda pendentes.
                </p>
                <button className="secondary" onClick={onReport}>
                  Ver meu relatório
                </button>
              </>
            )}
            <div className="editor-footer">
              <button
                className="secondary"
                disabled={step === 0}
                onClick={() => change((p) => ({ ...p, step: p.step - 1 }))}
              >
                <ChevronLeft size={18} /> Voltar
              </button>
              <button
                className="primary"
                onClick={() => {
                  change((p) => ({
                    ...p,
                    completed: [...new Set([...p.completed, step])],
                    step: Math.min(7, step + 1),
                  }));
                  void save();
                }}
              >
                {step === 7 ? "Concluir revisão" : "Continuar"}
                <ArrowRight size={18} />
              </button>
            </div>
          </section>
          <div className="tip">
            <BookOpen size={23} />
            <div>
              <strong>Uma orientação para esta etapa</strong>
              <p>
                {content.find((c) => c.context === (cat ?? "metas"))?.text ||
                  "Preencha no seu ritmo. Se não souber um valor, deixe em branco e retome depois. A consultoria pode ajudar na revisão."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
function Stat({
  title,
  value,
  dark = false,
}: {
  title: string;
  value: string | null | undefined;
  dark?: boolean;
}) {
  return (
    <div className={"stat " + (dark ? "dark" : "")}>
      <span>{title}</span>
      <strong>{money(value)}</strong>
      <small>Valores conhecidos · confira as pendências</small>
    </div>
  );
}
function DebtFields({
  debts,
  onChange,
}: {
  debts: Debt[];
  onChange: (v: Debt[]) => void;
}) {
  const edit = (i: number, k: string, v: any) =>
    onChange(debts.map((d, j) => (j === i ? { ...d, [k]: v } : d)));
  return (
    <details>
      <summary>Detalhes das dívidas · {debts.length} cadastradas</summary>
      <p>
        O saldo devedor não entra nas saídas mensais. Registre as parcelas no
        planejamento acima.
      </p>
      {debts.map((d, i) => (
        <section className="subcard" key={d.key}>
          <div className="form-grid">
            <label>
              Instituição
              <input
                value={d.institution}
                onChange={(e) => edit(i, "institution", e.target.value)}
              />
            </label>
            <label>
              Tipo de dívida
              <input
                value={d.kind}
                onChange={(e) => edit(i, "kind", e.target.value)}
              />
            </label>
            <Money
              label="Saldo devedor, se conhecido"
              value={d.balance}
              onChange={(v) => edit(i, "balance", v)}
            />
            <label>
              Parcelas restantes
              <input
                type="number"
                min="0"
                max="1200"
                value={d.installments ?? ""}
                onChange={(e) =>
                  edit(
                    i,
                    "installments",
                    e.target.value === "" ? null : Number(e.target.value),
                  )
                }
              />
            </label>
            <label>
              Data de término
              <input
                type="date"
                value={d.end ?? ""}
                onChange={(e) => edit(i, "end", e.target.value || null)}
              />
            </label>
            <label>
              Situação informada
              <input
                value={d.status}
                onChange={(e) => edit(i, "status", e.target.value)}
              />
            </label>
          </div>
          <label className="check">
            <input
              type="checkbox"
              checked={d.guaranteed}
              onChange={(e) => edit(i, "guaranteed", e.target.checked)}
            />{" "}
            Existe garantia
          </label>
          <label>
            Observações
            <textarea
              value={d.notes}
              onChange={(e) => edit(i, "notes", e.target.value)}
            />
          </label>
          <button
            className="link danger"
            onClick={() => {
              if (confirm("Excluir estes detalhes?"))
                onChange(debts.filter((_, j) => j !== i));
            }}
          >
            Excluir detalhes
          </button>
        </section>
      ))}
      <button
        className="secondary"
        onClick={() =>
          onChange([
            ...debts,
            {
              key: crypto.randomUUID(),
              institution: "Nova instituição",
              kind: "Empréstimo",
              balance: null,
              installments: null,
              end: null,
              guaranteed: false,
              status: "A informar",
              notes: "",
            },
          ])
        }
      >
        <Plus size={17} /> Cadastrar detalhes
      </button>
    </details>
  );
}
function GoalFields({
  goals,
  onChange,
}: {
  goals: Goal[];
  onChange: (v: Goal[]) => void;
}) {
  const edit = (i: number, k: string, v: any) =>
    onChange(goals.map((g, j) => (j === i ? { ...g, [k]: v } : g)));
  return (
    <>
      {goals.map((g, i) => (
        <section className="subcard" key={i}>
          <label>
            Meu objetivo
            <input
              value={g.title}
              onChange={(e) => edit(i, "title", e.target.value)}
            />
          </label>
          <div className="form-grid">
            <Money
              label="Valor da meta, se conhecido"
              value={g.amount}
              onChange={(v) => edit(i, "amount", v)}
            />
            <label>
              Prazo informado
              <input
                type="date"
                value={g.deadline ?? ""}
                onChange={(e) => edit(i, "deadline", e.target.value || null)}
              />
            </label>
          </div>
          <label>
            Plano de negociação
            <textarea
              value={g.negotiation}
              onChange={(e) => edit(i, "negotiation", e.target.value)}
              placeholder="Registre instituição, proposta em avaliação e próximos passos."
            />
          </label>
          <button
            className="link danger"
            onClick={() => {
              if (confirm("Excluir esta meta?"))
                onChange(goals.filter((_, j) => j !== i));
            }}
          >
            Excluir meta
          </button>
        </section>
      ))}
      <button
        className="secondary"
        onClick={() =>
          onChange([
            ...goals,
            {
              title: "Minha nova meta",
              amount: null,
              deadline: null,
              negotiation: "",
            },
          ])
        }
      >
        <Plus size={17} /> Adicionar meta
      </button>
    </>
  );
}
function Reports({ sid }: { sid: number }) {
  const [r, setR] = useState<any>(null),
    [mode, setMode] = useState("forecast"),
    [month, setMonth] = useState(""),
    [p, setP] = useState<Plan | null>(null),
    [notes, setNotes] = useState<any[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api("/reports/" + sid + "?mode=" + mode)
      .then((v) => {
        if (active) {
          setR(v);
          setMonth((m) => m || v.months[0].month);
        }
      })
      .catch((e) => setError(e.message));
    api<Plan>("/plans/" + sid)
      .then(setP)
      .catch(() => {});
    api<any[]>("/notes/" + sid)
      .then((n) => setNotes(n.filter((x) => !x.internal)))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [sid, mode]);
  const selected = r?.months.find((x: any) => x.month === month);
  const max = r
    ? Math.max(
        1,
        ...r.months.flatMap((m: any) => [Number(m.income), Number(m.outflow)]),
      )
    : 1;
  return (
    <>
      <Heading
        title="Meu relatório"
        action={
          <a
            className="primary"
            href={"/api/reports/" + sid + "/pdf?mode=" + mode}
          >
            <Download size={18} /> Baixar PDF
          </a>
        }
      >
        Veja suas finanças com clareza, mês a mês.
      </Heading>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="form-grid">
        <label>
          Tipo de valores
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="forecast">Previstos</option>
            <option value="actual">Realizados</option>
          </select>
        </label>
        {r && (
          <label>
            Mês selecionado
            <select value={month} onChange={(e) => setMonth(e.target.value)}>
              {r.months.map((x: any) => (
                <option key={x.month} value={x.month}>
                  {labelMonth(x.month)}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {r && (
        <>
          <p className="caption">
            {r.student.name} · Gerado em {date(r.generated_at)} · Valores{" "}
            {mode === "forecast" ? "previstos" : "realizados"}
          </p>
          {r.incomplete && (
            <p className="notice">
              Preenchimento incompleto. Os resultados são parciais e consideram
              somente valores informados.
            </p>
          )}
          <div className="stats">
            <Stat title="Entradas" value={selected?.income} />
            <Stat title="Saídas consideradas" value={selected?.outflow} />
            <Stat title="Sobra ou falta" value={selected?.balance} dark />
          </div>
          <section className="panel report">
            <div className="section-title">
              <h2>Entradas e saídas por mês</h2>
              <span className="legend">Azul: entradas · Dourado: saídas</span>
            </div>
            <div
              className="bar-chart"
              role="img"
              aria-label="Entradas e saídas; valores disponíveis abaixo em texto"
            >
              {r.months.map((x: any) => (
                <div key={x.month}>
                  <div className="bars">
                    <i
                      style={{
                        height:
                          Math.max(1, (Number(x.income) / max) * 100) + "%",
                      }}
                    />
                    <i
                      style={{
                        height:
                          Math.max(1, (Number(x.outflow) / max) * 100) + "%",
                      }}
                    />
                  </div>
                  <small>
                    {x.month.slice(5)}/{x.month.slice(2, 4)}
                  </small>
                </div>
              ))}
            </div>
          </section>
          <div className="report-grid">
            <section className="panel report">
              <h2>Sobra ou falta nos próximos meses</h2>
              {r.months.map((x: any) => (
                <div className="category-bar" key={x.month}>
                  <div>
                    <span>{labelMonth(x.month)}</span>
                    <strong>{money(x.balance)}</strong>
                  </div>
                  <div className="track">
                    <i
                      style={{
                        width: (Math.abs(Number(x.balance)) / max) * 100 + "%",
                        background:
                          Number(x.balance) < 0 ? "#a45135" : "#124a57",
                      }}
                    />
                  </div>
                </div>
              ))}
            </section>
            <section className="panel report">
              <h2>Despesas por categoria</h2>
              <p>{labelMonth(month)} · Valores de acompanhamento</p>
              {selected &&
                categories
                  .filter((c) => c.code !== "rendas")
                  .map((c) => (
                    <div className="category-bar" key={c.code}>
                      <div>
                        <span>{c.label}</span>
                        <strong>{money(selected.categories[c.code])}</strong>
                      </div>
                      <div className="track">
                        <i
                          style={{
                            width:
                              (Number(selected.categories[c.code]) /
                                Math.max(
                                  1,
                                  ...Object.values(selected.categories).map(
                                    Number,
                                  ),
                                )) *
                                100 +
                              "%",
                          }}
                        />
                      </div>
                    </div>
                  ))}
            </section>
          </div>
          <section className="panel report">
            <h2>Comprometimento da renda por categoria</h2>
            {selected &&
              categories
                .filter((c) => c.code !== "rendas")
                .map((c) => (
                  <div className="category-bar" key={c.code}>
                    <div>
                      <span>{c.label}</span>
                      <strong>
                        {selected.percentages[c.code] === null
                          ? "Indisponível"
                          : selected.percentages[c.code] + "%"}
                      </strong>
                    </div>
                    {selected.percentages[c.code] !== null && (
                      <div className="track">
                        <i
                          style={{
                            width:
                              (Number(selected.percentages[c.code]) /
                                Math.max(
                                  100,
                                  ...Object.values(selected.percentages).map(
                                    Number,
                                  ),
                                )) *
                                100 +
                              "%",
                            background: "#b18a58",
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))}
            <p className="caption">
              Renda zero ou ausente: percentual indisponível. Consignados e
              registros excluídos do orçamento são acompanhamento; não some os
              percentuais como composição das saídas.
            </p>
          </section>
          <section className="panel report">
            <h2>Planejamento dos 12 meses</h2>
            <div className="monthly">
              {r.months.map((x: any) => (
                <article key={x.month}>
                  <h3>{labelMonth(x.month)}</h3>
                  <p>
                    Entradas: <strong>{money(x.income)}</strong>
                  </p>
                  <p>
                    Saídas: <strong>{money(x.outflow)}</strong>
                  </p>
                  <p>
                    Sobra/falta: <strong>{money(x.balance)}</strong>
                  </p>
                  {x.incomplete && <small>Dados incompletos</small>}
                </article>
              ))}
            </div>
            <h3>Totais do período {r.incomplete && "· parciais"}</h3>
            <div className="stats">
              <Stat title="Entradas conhecidas" value={r.totals.income} />
              <Stat title="Saídas consideradas" value={r.totals.outflow} />
              <Stat title="Sobra ou falta" value={r.totals.balance} />
            </div>
          </section>
          {p && (
            <section className="panel report">
              <h2>Dívidas, metas e negociação</h2>
              {p.debts.length === 0 && (
                <p>Nenhuma dívida detalhada cadastrada.</p>
              )}
              {p.debts.map((d) => (
                <p key={d.key}>
                  <strong>{d.institution}</strong> · {d.kind} · saldo{" "}
                  {money(d.balance)} · parcelas{" "}
                  {d.installments ?? "não informado"} · término{" "}
                  {d.end ?? "não informado"} · garantia{" "}
                  {d.guaranteed ? "sim" : "não"} · {d.status}
                  <br />
                  {d.notes}
                </p>
              ))}
              {p.goals.map((g, i) => (
                <p key={i}>
                  <strong>{g.title}</strong> · {money(g.amount)} · prazo{" "}
                  {g.deadline ?? "não informado"}
                  <br />
                  {g.negotiation}
                </p>
              ))}
              <h3>Orientações liberadas pela consultoria</h3>
              {notes.length === 0 ? (
                <p>Nenhuma orientação liberada.</p>
              ) : (
                notes.map((n) => (
                  <p className="preserve" key={n.id}>
                    {n.text}
                  </p>
                ))
              )}
            </section>
          )}
        </>
      )}
    </>
  );
}
function Guides() {
  const [items, setItems] = useState<any[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    api<any[]>("/contents")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <Heading title="Orientações">
        Conteúdos revisados para apoiar seu planejamento.
      </Heading>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!items.length && !error && (
        <section className="panel empty">
          <BookOpen />
          <h2>Conteúdos em preparação</h2>
          <p>
            As orientações aparecerão após revisão e publicação administrativa.
          </p>
        </section>
      )}
      <div className="report-grid">
        {items.map((c) => (
          <article className="panel report" key={c.id}>
            <BookOpen />
            <h2>{c.title}</h2>
            <p className="preserve">{c.text}</p>
            <small>
              {c.module} · {c.lesson}
              <br />
              {c.reference} · versão {c.version}
            </small>
          </article>
        ))}
      </div>
    </>
  );
}
function Account({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [support, setSupport] = useState(""),
    [history, setHistory] = useState<any[]>([]),
    [message, setMessage] = useState(""),
    [old, setOld] = useState(""),
    [password, setPassword] = useState("");
  useEffect(() => {
    api("/support").then((r) => setSupport(r.contact));
    api<any[]>("/users/" + user.id + "/access-history")
      .then(setHistory)
      .catch(() => {});
  }, [user.id]);
  return (
    <>
      <Heading title="Minha conta e ajuda">
        Suas informações e o caminho para falar com a equipe.
      </Heading>
      <div className="report-grid">
        <section className="panel report">
          <h2>Minha conta</h2>
          <dl>
            <dt>Nome</dt>
            <dd>{user.name}</dd>
            <dt>Celular</dt>
            <dd>{user.phone}</dd>
            <dt>E-mail</dt>
            <dd>{user.email || "Não informado"}</dd>
            <dt>Perfis</dt>
            <dd>{user.roles.join(", ")}</dd>
            <dt>Acesso do aluno</dt>
            <dd>
              {user.roles.includes("aluno")
                ? user.status
                : "Validade anual não se aplica à equipe"}
            </dd>
            {user.roles.includes("aluno") && (
              <>
                <dt>Válido até, Brasília</dt>
                <dd>{date(user.expires_at)}</dd>
              </>
            )}
          </dl>
          {user.roles.includes("aluno") && (
            <button
              className="primary"
              onClick={async () => {
                try {
                  setMessage((await api("/renewals", "POST")).message);
                } catch (e) {
                  setMessage((e as Error).message);
                }
              }}
            >
              Solicitar renovação
            </button>
          )}
          <h3>Histórico de liberações e renovações</h3>
          {history.map((h) => (
            <p key={h.id}>
              {date(h.created_at)} · {h.action} · vencimento{" "}
              {date(h.expires_at)}
            </p>
          ))}
        </section>
        <section className="panel report">
          <HeartHandshake />
          <h2>Estamos aqui para ajudar.</h2>
          <p className="preserve">{support}</p>
          <p>
            A equipe verificará sua identidade para recuperar seu acesso. Nunca
            compartilhe sua senha.
          </p>
          <h3>Trocar senha</h3>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api("/auth/password", "POST", {
                  old_password: old,
                  password,
                });
                onLogout();
              } catch (e) {
                setMessage((e as Error).message);
              }
            }}
          >
            <label>
              Senha atual
              <input
                type="password"
                autoComplete="current-password"
                value={old}
                onChange={(e) => setOld(e.target.value)}
                required
              />
            </label>
            <label>
              Nova senha
              <input
                type="password"
                autoComplete="new-password"
                minLength={6}
                maxLength={200}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <small>
                6 a 200 caracteres. Você entrará novamente depois da troca.
              </small>
            </label>
            <button className="secondary">Alterar senha</button>
          </form>
        </section>
      </div>
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
    </>
  );
}
function UserForm({ admin, onDone }: { admin: boolean; onDone: () => void }) {
  const [form, setForm] = useState({
      name: "",
      phone: "",
      email: "",
      password: "",
      roles: ["aluno"],
    }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <form
      className="panel report"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        try {
          await api("/users", "POST", { ...form, email: form.email || null });
          onDone();
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2>Novo cadastro</h2>
      <p>O aluno fica pendente até liberação explícita do administrador.</p>
      <div className="form-grid">
        {[
          ["name", "Nome completo", "text"],
          ["phone", "Celular com DDD (+55 automático)", "tel"],
          ["email", "E-mail, opcional", "email"],
          ["password", "Senha inicial (6 a 200 caracteres)", "password"],
        ].map(([key, label, type]) => (
          <label key={key}>
            {label}
            <input
              type={type}
              value={form[key as "name"]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required={key !== "email"}
              minLength={key === "password" ? 6 : undefined}
              maxLength={key === "password" ? 200 : undefined}
              autoComplete={key === "password" ? "new-password" : undefined}
            />
            {key === "phone" && (
              <small>
                Brasil: +55 automático. Para outro país, digite + e o código.
              </small>
            )}
          </label>
        ))}
      </div>
      {admin && (
        <fieldset>
          <legend>Perfis acumulados</legend>
          {["aluno", "consultor", "vendedor", "administrador"].map((r) => (
            <label className="check" key={r}>
              <input
                type="checkbox"
                checked={form.roles.includes(r)}
                onChange={(e) =>
                  setForm({
                    ...form,
                    roles: e.target.checked
                      ? [...form.roles, r]
                      : form.roles.filter((v) => v !== r),
                  })
                }
              />
              {r}
            </label>
          ))}
        </fieldset>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button className="primary" disabled={busy || !form.roles.length}>
        {busy ? "Salvando…" : "Salvar cadastro"}
      </button>
    </form>
  );
}
function Team({ user, onOpen }: { user: User; onOpen: (u: User) => void }) {
  const [q, setQ] = useState(""),
    [status, setStatus] = useState(""),
    [completion, setCompletion] = useState(""),
    [page, setPage] = useState(1),
    [data, setData] = useState<any>({ items: [], total: 0 }),
    [error, setError] = useState(""),
    [rev, setRev] = useState(0),
    [create, setCreate] = useState(false),
    [editing, setEditing] = useState<User | null>(null),
    [savedMessage, setSavedMessage] = useState(""),
    [student, setStudent] = useState<User | null>(null);
  const finance = user.roles.some((r) =>
      ["consultor", "administrador"].includes(r),
    ),
    admin = user.roles.includes("administrador");
  useEffect(() => {
    let active = true;
    api(
      "/users?q=" +
        encodeURIComponent(q) +
        "&status_filter=" +
        status +
        "&completion=" +
        completion +
        "&page=" +
        page,
    )
      .then((r) => {
        if (active) setData(r);
      })
      .catch((e) => setError(e.message));
    return () => {
      active = false;
    };
  }, [q, status, completion, page, rev]);
  return (
    <>
      <Heading
        title="Alunos e atendimentos"
        action={
          (admin || user.roles.includes("vendedor")) && (
            <button className="primary" onClick={() => setCreate(!create)}>
              <Plus size={17} /> Cadastrar aluno
            </button>
          )
        }
      >
        Acompanhe cada pessoa com cuidado e atenção.
      </Heading>
      {create && (
        <UserForm
          admin={admin}
          onDone={() => {
            setCreate(false);
            setRev(rev + 1);
          }}
        />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {savedMessage && (
        <p className="notice" role="status">
          {savedMessage}
        </p>
      )}
      {editing && (
        <ProfileEditor
          key={editing.id}
          user={editing}
          onCancel={() => {
            setEditing(null);
            setRev((v) => v + 1);
          }}
          onSaved={(updated) => {
            setEditing(null);
            setSavedMessage("Cadastro atualizado com sucesso.");
            setRev((v) => v + 1);
            if (updated.id === user.id && updated.phone !== user.phone)
              window.location.reload();
          }}
        />
      )}
      <section className="panel report">
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
            Situação
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Todas</option>
              {["pendente", "ativo", "vencido", "bloqueado", "revogado"].map(
                (s) => (
                  <option key={s}>{s}</option>
                ),
              )}
            </select>
          </label>
          {finance && (
            <label>
              Preenchimento
              <select
                value={completion}
                onChange={(e) => {
                  setCompletion(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos</option>
                <option value="pendente">Pendente</option>
                <option value="concluido">Concluído</option>
              </select>
            </label>
          )}
        </div>
        {data.items.map((s: User) => (
          <article className="person-row" key={s.id}>
            <span className="avatar">{s.name[0]}</span>
            <div className="grow">
              <strong>{s.name}</strong>
              <small>
                {s.phone} {s.email && "· " + s.email}
              </small>
            </div>
            <div>
              <span className="badge">{s.status}</span>
              <small>Até {date(s.expires_at)}</small>
            </div>
            <div className="actions">
              {finance && (
                <>
                  <button className="secondary" onClick={() => onOpen(s)}>
                    Planejamento <ChevronRight size={16} />
                  </button>
                  <button
                    className="secondary"
                    onClick={() => setStudent(student?.id === s.id ? null : s)}
                  >
                    Atendimento
                  </button>
                </>
              )}
              {admin && (
                <button
                  className="secondary"
                  onClick={() => {
                    setSavedMessage("");
                    setEditing(s);
                  }}
                >
                  Editar cadastro
                </button>
              )}
              {admin && (
                <AccessControl student={s} onDone={() => setRev(rev + 1)} />
              )}
            </div>
          </article>
        ))}
        {!data.items.length && <p>Nenhum aluno encontrado.</p>}
        <div className="pagination">
          <span>
            {data.total} alunos · página {page}
          </span>
          <button
            className="secondary"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </button>
          <button
            className="secondary"
            disabled={page * 20 >= data.total}
            onClick={() => setPage(page + 1)}
          >
            Próxima
          </button>
        </div>
      </section>
      {student && <Notes key={student.id} student={student} />}
    </>
  );
}
function ProfileEditor({
  user,
  onCancel,
  onSaved,
}: {
  user: User;
  onCancel: () => void;
  onSaved: (user: User) => void;
}) {
  const original = { name: user.name, phone: user.phone, email: user.email };
  const [name, setName] = useState(user.name),
    [phone, setPhone] = useState(user.phone),
    [email, setEmail] = useState(user.email ?? ""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
    heading.current?.scrollIntoView({ block: "start" });
  }, []);
  return (
    <form
      className="panel report"
      aria-label="Editar cadastro do aluno"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          const updated = await api<User>(
            "/users/" + user.id + "/profile",
            "PUT",
            { name, phone, email: email || null, original },
          );
          onSaved(updated);
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2 ref={heading} tabIndex={-1}>
        Editar cadastro · {user.name}
      </h2>
      <label>
        Nome completo
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          minLength={2}
          maxLength={160}
        />
      </label>
      <label>
        Celular com DDD
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          maxLength={40}
        />
        <small>
          Brasil: +55 automático. Para outro país, digite + e o código. Ao
          alterar o celular de acesso, as sessões dessa pessoa serão encerradas.
        </small>
      </label>
      <label>
        E-mail, opcional
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          maxLength={254}
        />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="actions">
        <button className="primary" disabled={busy}>
          {busy ? "Salvando…" : "Salvar alterações"}
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => {
            if (
              name !== user.name ||
              phone !== user.phone ||
              email !== (user.email ?? "")
            ) {
              if (!confirm("Descartar as alterações deste cadastro?")) return;
            }
            onCancel();
          }}
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
function AccessControl({
  student,
  onDone,
}: {
  student: User;
  onDone: () => void;
}) {
  const [action, setAction] = useState("ativar"),
    [expiry, setExpiry] = useState(""),
    [error, setError] = useState("");
  return (
    <details className="access">
      <summary>Gerenciar acesso</summary>
      <label>
        Ação
        <select value={action} onChange={(e) => setAction(e.target.value)}>
          {["ativar", "renovar", "bloquear", "revogar"].map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
      </label>
      {["ativar", "renovar"].includes(action) && (
        <label>
          Vencimento personalizado, opcional
          <input
            type="date"
            value={expiry}
            onChange={(e) => setExpiry(e.target.value)}
          />
          <small>Em branco: um ano de calendário.</small>
        </label>
      )}
      <button
        className="secondary"
        onClick={async () => {
          if (!confirm(`Confirmar ${action} o acesso de ${student.name}?`))
            return;
          try {
            await api("/users/" + student.id + "/access", "POST", {
              action,
              expires_at: expiry ? expiry + "T23:59:59-03:00" : null,
            });
            setError("");
            onDone();
          } catch (e) {
            setError((e as Error).message);
          }
        }}
      >
        Confirmar ação
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </details>
  );
}
function Notes({ student }: { student: User }) {
  const [notes, setNotes] = useState<any[]>([]),
    [history, setHistory] = useState<any[]>([]),
    [text, setText] = useState(""),
    [internal, setInternal] = useState(true),
    [error, setError] = useState(""),
    [rev, setRev] = useState(0),
    [page, setPage] = useState(1);
  useEffect(() => {
    api<any[]>("/notes/" + student.id)
      .then(setNotes)
      .catch((e) => setError(e.message));
    api<any[]>("/audit?subject=" + student.id + "&page=" + page)
      .then(setHistory)
      .catch((e) => setError(e.message));
  }, [student.id, rev, page]);
  return (
    <section className="panel report">
      <h2>Atendimento · {student.name}</h2>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await api("/notes/" + student.id, "POST", { text, internal });
            setText("");
            setRev(rev + 1);
          } catch (e) {
            setError((e as Error).message);
          }
        }}
      >
        <label>
          Registro de atendimento
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
            maxLength={10000}
          />
        </label>
        <label>
          Visibilidade
          <select
            value={String(internal)}
            onChange={(e) => setInternal(e.target.value === "true")}
          >
            <option value="true">Anotação interna · somente equipe</option>
            <option value="false">Orientação liberada · aluno e PDF</option>
          </select>
        </label>
        <button className="primary">Registrar atendimento</button>
      </form>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notes.map((n) => (
        <article className="note" key={n.id}>
          <span className="badge">
            {n.internal ? "Interno · equipe" : "Visível ao aluno"}
          </span>
          <p className="preserve">{n.text}</p>
          <small>
            {date(n.created_at)} · responsável #{n.author_id}
          </small>
        </article>
      ))}
      <details>
        <summary>Histórico de alterações</summary>
        {history.map((a) => (
          <details key={a.id}>
            <summary>
              {date(a.created_at)} · {a.action} · responsável #{a.actor}
            </summary>
            <pre>{JSON.stringify(a.details, null, 2)}</pre>
          </details>
        ))}
        <div className="pagination">
          <button
            className="secondary"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </button>
          <span>Página {page}</span>
          <button
            className="secondary"
            disabled={history.length < 20}
            onClick={() => setPage(page + 1)}
          >
            Próxima
          </button>
        </div>
      </details>
    </section>
  );
}
function Admin() {
  const [tab, setTab] = useState("renewals"),
    [items, setItems] = useState<any[]>([]),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [rev, setRev] = useState(0),
    [team, setTeam] = useState<any>({ items: [], total: 0 }),
    [page, setPage] = useState(1),
    [contact, setContact] = useState(""),
    [csv, setCsv] = useState(""),
    [preview, setPreview] = useState<any>(null),
    [content, setContent] = useState<any>(null);
  useEffect(() => {
    setItems([]);
    const load = async () => {
      if (tab === "renewals") setItems(await api("/renewals"));
      if (tab === "contents") setItems(await api("/contents?all=true"));
      if (tab === "audit") setItems(await api("/audit?page=" + page));
      if (tab === "team") setTeam(await api("/users?team=true&page=" + page));
      if (tab === "support") setContact((await api("/support")).contact);
    };
    load().catch((e) => setError(e.message));
  }, [tab, rev, page]);
  async function run(fn: () => Promise<any>) {
    setError("");
    setMessage("");
    try {
      await fn();
      setMessage("Operação concluída.");
      setRev((v) => v + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Heading title="Administração">
        Acessos, equipe e conteúdos em um só lugar.
      </Heading>
      <div className="tabs" aria-label="Áreas administrativas">
        {[
          ["renewals", "Renovações"],
          ["team", "Equipe e perfis"],
          ["import", "Importar CSV"],
          ["contents", "Conteúdos"],
          ["support", "Suporte"],
          ["audit", "Auditoria"],
        ].map(([k, l]) => (
          <button
            className={tab === k ? "selected" : ""}
            key={k}
            aria-pressed={tab === k}
            onClick={() => {
              setTab(k);
              setPage(1);
              setError("");
              setMessage("");
              setContent(null);
            }}
          >
            {l}
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
      <section className="panel report">
        {tab === "renewals" && (
          <>
            <h2>Solicitações de renovação</h2>
            {!items.length && <p>Nenhuma solicitação registrada.</p>}
            {items.map((r) => (
              <div className="person-row" key={r.id}>
                <div className="grow">
                  <strong>{r.name}</strong>
                  <small>
                    {date(r.created_at)} · {r.status}
                  </small>
                </div>
                {r.status === "pendente" && (
                  <button
                    className="primary"
                    onClick={() => {
                      if (
                        confirm("Aprovar a renovação por um ano de calendário?")
                      )
                        void run(() =>
                          api("/users/" + r.student_id + "/access", "POST", {
                            action: "renovar",
                          }),
                        );
                    }}
                  >
                    Aprovar renovação
                  </button>
                )}
              </div>
            ))}
          </>
        )}
        {tab === "team" && (
          <>
            <h2>Cadastros e perfis acumulados</h2>
            <UserForm admin onDone={() => setRev(rev + 1)} />
            {team.items.map((u: User) => (
              <TeamUser key={u.id} user={u} onDone={() => setRev(rev + 1)} />
            ))}
            <div className="pagination">
              <span>
                {team.total} contas · página {page}
              </span>
              <button
                className="secondary"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Anterior
              </button>
              <button
                className="secondary"
                disabled={page * 20 >= team.total}
                onClick={() => setPage(page + 1)}
              >
                Próxima
              </button>
            </div>
          </>
        )}
        {tab === "support" && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(() => api("/support", "PUT", { contact }));
            }}
          >
            <h2>Contato de suporte</h2>
            <label>
              Telefone, e-mail e instruções de atendimento
              <textarea
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                maxLength={500}
              />
            </label>
            <button className="primary">Salvar contato</button>
          </form>
        )}
        {tab === "audit" && (
          <>
            <h2>Auditoria</h2>
            {items.map((a) => (
              <details key={a.id}>
                <summary>
                  {date(a.created_at)} · {a.action} · responsável #
                  {a.actor ?? "sistema"} · registro #{a.subject ?? "geral"}
                </summary>
                <pre>{JSON.stringify(a.details, null, 2)}</pre>
              </details>
            ))}
            <div className="pagination">
              <button
                className="secondary"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Anterior
              </button>
              <span>Página {page}</span>
              <button
                className="secondary"
                disabled={items.length < 20}
                onClick={() => setPage(page + 1)}
              >
                Próxima
              </button>
            </div>
          </>
        )}
        {tab === "import" && (
          <>
            <h2>Importar alunos com segurança</h2>
            <p>
              CSV com colunas name,phone,email. Celulares internacionais. Contas
              ficam pendentes, sem ativação automática. O primeiro acesso usa
              recuperação controlada.
            </p>
            <label>
              Arquivo CSV
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setCsv(await file.text());
                    setPreview(null);
                  }
                }}
              />
            </label>
            <label>
              Conteúdo do arquivo
              <textarea
                rows={8}
                value={csv}
                onChange={(e) => {
                  setCsv(e.target.value);
                  setPreview(null);
                }}
              />
            </label>
            <button
              className="secondary"
              disabled={!csv.trim()}
              onClick={() =>
                void run(async () =>
                  setPreview(
                    await api("/import", "POST", { text: csv, commit: false }),
                  ),
                )
              }
            >
              Validar e visualizar prévia
            </button>
            {preview && (
              <>
                <p>
                  {preview.count} linhas ·{" "}
                  {preview.rows.filter((r: any) => !r.valid).length} inválidas
                </p>
                <div className="preview">
                  {preview.rows.map((r: any) => (
                    <p key={r.line} className={!r.valid ? "error-text" : ""}>
                      Linha {r.line} · {r.name} · {r.valid ? r.phone : r.error}
                    </p>
                  ))}
                </div>
                <button
                  className="primary"
                  disabled={
                    preview.committed || preview.rows.some((r: any) => !r.valid)
                  }
                  onClick={() => {
                    if (
                      confirm("Confirmar a importação dos cadastros validados?")
                    )
                      void run(async () =>
                        setPreview(
                          await api("/import", "POST", {
                            text: csv,
                            commit: true,
                          }),
                        ),
                      );
                  }}
                >
                  {preview.committed
                    ? "Importação concluída"
                    : "Confirmar importação"}
                </button>
              </>
            )}
          </>
        )}
        {tab === "contents" && (
          <>
            <div className="section-title">
              <h2>Conteúdos do curso</h2>
              <button
                className="secondary"
                onClick={() =>
                  setContent({
                    title: "",
                    text: "",
                    module: "",
                    lesson: "",
                    reference: "",
                    context: "rendas",
                    status: "rascunho",
                    version: 1,
                  })
                }
              >
                <Plus size={16} /> Novo conteúdo
              </button>
            </div>
            <p>
              Revise a referência e o texto antes de publicar. Afirmações
              jurídicas e bancárias exigem validação atualizada.
            </p>
            {items.map((c) => (
              <div className="person-row" key={c.id}>
                <div className="grow">
                  <strong>{c.title}</strong>
                  <small>
                    {c.status} · versão {c.version} · aprovação #
                    {c.approved_by ?? "pendente"}
                  </small>
                </div>
                <button className="secondary" onClick={() => setContent(c)}>
                  Revisar
                </button>
              </div>
            ))}
            {content && (
              <ContentForm
                key={content.id ?? "new"}
                content={content}
                onSave={async (values) => {
                  await run(async () => {
                    await api(
                      "/contents" + (content.id ? "/" + content.id : ""),
                      content.id ? "PUT" : "POST",
                      values,
                    );
                    setContent(null);
                  });
                }}
              />
            )}
          </>
        )}
      </section>
    </>
  );
}
function TeamUser({ user, onDone }: { user: User; onDone: () => void }) {
  const [roles, setRoles] = useState(user.roles),
    [message, setMessage] = useState("");
  async function run(fn: () => Promise<any>) {
    try {
      await fn();
      onDone();
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <details>
      <summary>
        {user.name} · {user.phone} · {user.roles.join(", ")} ·{" "}
        {user.enabled ? "Conta habilitada" : "Conta desativada"}
      </summary>
      <fieldset>
        <legend>Perfis</legend>
        {["aluno", "consultor", "vendedor", "administrador"].map((r) => (
          <label className="check" key={r}>
            <input
              type="checkbox"
              checked={roles.includes(r)}
              onChange={(e) =>
                setRoles(
                  e.target.checked
                    ? [...roles, r]
                    : roles.filter((x) => x !== r),
                )
              }
            />
            {r}
          </label>
        ))}
      </fieldset>
      <div className="actions">
        <button
          className="secondary"
          disabled={!roles.length}
          onClick={() =>
            void run(async () => {
              await api("/users/" + user.id + "/roles", "PUT", { roles });
              setMessage("Perfis salvos. Sessões anteriores encerradas.");
            })
          }
        >
          Salvar perfis
        </button>
        <button
          className="secondary"
          onClick={() => {
            if (
              confirm(
                user.enabled
                  ? "Desativar a conta e encerrar sessões?"
                  : "Reativar esta conta?",
              )
            )
              void run(() =>
                api("/users/" + user.id + "/enabled", "PUT", {
                  enabled: !user.enabled,
                }),
              );
          }}
        >
          {user.enabled ? "Desativar conta" : "Reativar conta"}
        </button>
        <button
          className="secondary"
          onClick={() => {
            if (
              confirm(
                "Você verificou a identidade da pessoa pelo procedimento administrativo?",
              )
            )
              void run(async () => {
                const r = await api("/users/" + user.id + "/recovery", "POST");
                setMessage(r.message + " Código: " + r.token);
              });
          }}
        >
          Emitir código de recuperação
        </button>
        <button
          className="secondary danger"
          onClick={() => {
            const confirmation = prompt(
              "A exclusão remove dados e é diferente de revogar. Após verificar autorização e retenção, digite EXCLUIR " +
                user.phone,
            );
            if (!confirmation) return;
            const reason = prompt("Motivo documentado (mínimo 10 caracteres):");
            if (reason)
              void run(() =>
                api("/users/" + user.id, "DELETE", { confirmation, reason }),
              );
          }}
        >
          Excluir dados da conta
        </button>
      </div>
      {user.roles.includes("aluno") && (
        <AccessControl student={user} onDone={onDone} />
      )}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
    </details>
  );
}
function ContentForm({
  content,
  onSave,
}: {
  content: any;
  onSave: (values: any) => Promise<void>;
}) {
  const [form, setForm] = useState({ ...content }),
    [history, setHistory] = useState<any[]>([]);
  useEffect(() => {
    setForm({ ...content });
    if (content.id)
      api<any[]>("/contents/" + content.id + "/versions")
        .then(setHistory)
        .catch(() => {});
  }, [content]);
  return (
    <form
      className="subcard"
      onSubmit={(e) => {
        e.preventDefault();
        const { id, approved_by, ...values } = form;
        void onSave(values);
      }}
    >
      <h3>Revisão de conteúdo</h3>
      {[
        ["title", "Título"],
        ["module", "Módulo"],
        ["lesson", "Aula"],
        ["reference", "Referência ou marcação de tempo"],
      ].map(([key, label]) => (
        <label key={key}>
          {label}
          <input
            value={form[key]}
            onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            required
          />
        </label>
      ))}
      <label>
        Texto revisado
        <textarea
          rows={6}
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
          required
        />
      </label>
      <label>
        Etapa
        <select
          value={form.context}
          onChange={(e) => setForm({ ...form, context: e.target.value })}
        >
          {categories.map((c) => (
            <option key={c.code} value={c.code}>
              {c.label}
            </option>
          ))}
          <option value="metas">Metas</option>
        </select>
      </label>
      <label>
        Situação do conteúdo
        <select
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          <option value="rascunho">Rascunho</option>
          <option value="publicado">Publicado · aprovar esta versão</option>
        </select>
      </label>
      <button className="primary">Salvar revisão</button>
      {history.length > 0 && (
        <details>
          <summary>Histórico de versões</summary>
          {history.map((v) => (
            <details key={v.id}>
              <summary>Versão {v.version}</summary>
              <pre>{JSON.stringify(v.snapshot, null, 2)}</pre>
            </details>
          ))}
        </details>
      )}
    </form>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
