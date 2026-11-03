export type User = {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  roles: string[];
  status: string;
  enabled: boolean;
  expires_at: string | null;
};
export type Entry = {
  key: string;
  category: string;
  label: string;
  month: string;
  forecast: string | null;
  actual: string | null;
  deducted: boolean;
  method: string;
  absent: boolean;
};
export type Debt = {
  key: string;
  institution: string;
  kind: string;
  balance: string | null;
  installments: number | null;
  end: string | null;
  guaranteed: boolean;
  status: string;
  notes: string;
};
export type Goal = {
  title: string;
  amount: string | null;
  deadline: string | null;
  negotiation: string;
};
export type Plan = {
  id: number;
  user_id: number;
  version: number;
  start: string;
  selected_month: string;
  step: number;
  completed: number[];
  card_mode: string;
  entries: Entry[];
  debts: Debt[];
  goals: Goal[];
};
let csrf = "";
export const setCsrf = (v: string) => (csrf = v);
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T = any>(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  let r: Response;
  try {
    r = await fetch("/api" + path, {
      method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
  } catch {
    throw new ApiError(
      0,
      "Não foi possível conectar. Seus valores continuam nesta página. Confira a conexão e tente novamente.",
    );
  }
  if (!r.ok) {
    const b = await r.json().catch(() => ({}));
    throw new ApiError(
      r.status,
      typeof b.detail === "string"
        ? b.detail
        : Array.isArray(b.detail)
          ? b.detail
              .map((x: any) => x.loc.slice(1).join(".") + ": " + x.msg)
              .join("; ")
          : "Não foi possível concluir a operação.",
    );
  }
  return r.json();
}
export const money = (v: string | number | null | undefined) =>
  v == null
    ? "Não informado"
    : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
export const date = (v: string | null) =>
  v
    ? new Date(v).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" })
    : "Não definido";
export const labelMonth = (v: string) =>
  new Date(v + "-15T12:00:00Z").toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
export function months(start: string) {
  const [y, m] = start.split("-").map(Number);
  return Array.from(
    { length: 12 },
    (_, i) =>
      `${y + Math.floor((m - 1 + i) / 12)}-${String(((m - 1 + i) % 12) + 1).padStart(2, "0")}`,
  );
}
