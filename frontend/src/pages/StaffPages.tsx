import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router";
import { z } from "zod";
import { CameraScanner } from "../features/scanner/CameraScanner";
import { api, download, errorMessage, EVENT_SLUG, getStaffRole, isAuthenticated, setAuth, staffHome, type StaffRole } from "../shared/api";
import { Empty, Loading, Status } from "../shared/ui";

const loginSchema = z.object({ username: z.string().min(1, "Введите логин"), password: z.string().min(12, "Минимум 12 символов") });
type LoginValues = z.infer<typeof loginSchema>;

export function Protected({ children, roles }: { children: React.ReactNode; roles: StaffRole[] }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  const role = getStaffRole();
  return role && roles.includes(role) ? children : <Navigate to={staffHome(role)} replace />;
}

export function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });
  async function submit(values: LoginValues) {
    setError("");
    try {
      const result = await api<{ access_token: string; csrf_token: string; user: { role: string } }>("/auth/login", { method: "POST", body: JSON.stringify(values) });
      setAuth(result.access_token, result.csrf_token);
      navigate(result.user.role === "ADMIN" ? "/admin" : "/operator/scanner");
    } catch (caught) { setError(errorMessage(caught)); }
  }
  return <section><h1>Вход для организаторов</h1><form onSubmit={handleSubmit(submit)}><label>Логин<input autoComplete="username" {...register("username")} /></label>{errors.username && <span className="field-error">{errors.username.message}</span>}<label>Пароль<input type="password" autoComplete="current-password" {...register("password")} /></label>{errors.password && <span className="field-error">{errors.password.message}</span>}{error && <Status type="error">{error}</Status>}<button disabled={isSubmitting}>{isSubmitting ? "Входим…" : "Войти"}</button></form></section>;
}

type ScanResult = { result: string; full_name: string; study_group: string; institute: string; event_type: string; previous_status: string; new_status: string; occurred_at: string };
function tokenFromCode(code: string) { try { const url = new URL(code); return url.pathname.split("/").filter(Boolean).at(-1) ?? code; } catch { return code.trim(); } }

export function ScannerPage() {
  const [manual, setManual] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const mutation = useMutation({ mutationFn: (code: string) => api<ScanResult>("/operator/scans", { method: "POST", body: JSON.stringify({ token: tokenFromCode(code), device_info: { user_agent: navigator.userAgent } }), headers: { "Idempotency-Key": crypto.randomUUID() } }), onSuccess: data => { setResult(data); navigator.vibrate?.(100); }, onError: () => navigator.vibrate?.([150, 80, 150]) });
  return <section className="wide"><h1>QR-сканер</h1><CameraScanner onCode={code => !mutation.isPending && mutation.mutate(code)} /><div className="manual"><label>Ручной ввод кода<input value={manual} onChange={event => setManual(event.target.value)} /></label><button disabled={!manual || mutation.isPending} onClick={() => mutation.mutate(manual)}>Проверить</button></div>{mutation.isPending && <Status>Проверяем QR-код…</Status>}{mutation.error && <Status type="error">{errorMessage(mutation.error)}</Status>}{result && <Status type="success"><strong>{result.event_type === "ENTRY" ? "Вход разрешён" : "Выход зарегистрирован"}</strong><br />{result.full_name} · {result.study_group} · {result.institute}<br />{result.previous_status} → {result.new_status}</Status>}<Link to="/operator/recent">Последние операции</Link></section>;
}

export function RecentScansPage() {
  const query = useQuery({ queryKey: ["recent-scans"], queryFn: () => api<{ items: Array<{ id: string; result: string; error_code?: string; occurred_at: string; response?: ScanResult }> }>("/operator/scans/recent") });
  if (query.isLoading) return <Loading />;
  return <section><h1>Последние операции</h1>{query.data?.items.length ? <ul className="list">{query.data.items.map(item => <li key={item.id}><strong>{item.result === "SUCCESS" ? item.response?.full_name : item.error_code}</strong><time>{new Date(item.occurred_at).toLocaleTimeString("ru-RU")}</time></li>)}</ul> : <Empty>Операций пока нет</Empty>}</section>;
}

function useEvent() { return useQuery({ queryKey: ["event"], queryFn: () => api<{ id: string; name: string }>(`/public/events/${EVENT_SLUG}`) }); }

export function AdminPage() {
  const event = useEvent();
  const stats = useQuery({ queryKey: ["stats", event.data?.id], enabled: Boolean(event.data), refetchInterval: 10_000, queryFn: () => api<Record<string, number | string>>(`/admin/statistics/summary?event_id=${event.data?.id}`) });
  if (event.isLoading || stats.isLoading) return <Loading />;
  if (event.error || stats.error) return <Status type="error">{errorMessage(event.error ?? stats.error)}</Status>;
  const cards = [["Студентов", stats.data?.total_students], ["Зарегистрировано", stats.data?.registered], ["Сейчас внутри", stats.data?.inside], ["Уникальных посетителей", stats.data?.unique_visitors], ["Входов", stats.data?.entries], ["Ошибок сканирования", stats.data?.scan_errors]];
  return <section className="wide"><p className="eyebrow">Администрирование</p><h1>{event.data?.name}</h1><div className="stats">{cards.map(([label, value]) => <article key={label}><strong>{value}</strong><span>{label}</span></article>)}</div><nav className="admin-nav"><Link to="/admin/imports">Импорт студентов</Link><Link to="/admin/students">Студенты</Link><Link to="/admin/users">Операторы</Link><Link to="/admin/schedule">Расписание</Link><Link to="/admin/map">Карта</Link><button className="secondary" onClick={() => download(`/admin/exports/attendance.xlsx?event_id=${event.data?.id}`, "attendance.xlsx")}>Экспорт посещений</button></nav></section>;
}

type Batch = { id: string; status: string; total_rows: number; error_rows: number; warning_rows: number; created_rows: number; updated_rows: number; unchanged_rows: number; deactivated_rows: number; preview_version: string };
export function ImportPage() {
  const event = useEvent();
  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<Batch | null>(null);
  const [error, setError] = useState("");
  async function upload() { if (!file || !event.data) return; setError(""); const body = new FormData(); body.append("event_id", event.data.id); body.append("file", file); try { setBatch(await api<Batch>("/admin/imports", { method: "POST", body })); } catch (caught) { setError(errorMessage(caught)); } }
  async function confirm() { if (!batch) return; try { setBatch(await api<Batch>(`/admin/imports/${batch.id}/confirm`, { method: "POST", body: JSON.stringify({ preview_version: batch.preview_version, accept_warnings: true, confirm_deactivations: true, confirmation_phrase: batch.deactivated_rows >= 100 ? "ДЕАКТИВИРОВАТЬ" : null }), headers: { "Idempotency-Key": crypto.randomUUID() } })); } catch (caught) { setError(errorMessage(caught)); } }
  return <section className="wide"><h1>Импорт студентов</h1><div className="upload"><input aria-label="Файл XLSX" type="file" accept=".xlsx" onChange={event => setFile(event.target.files?.[0] ?? null)} /><button disabled={!file || !event.data} onClick={upload}>Проверить файл</button></div>{error && <Status type="error">{error}</Status>}{batch && <><div className="stats"><article><strong>{batch.created_rows}</strong><span>Добавится</span></article><article><strong>{batch.updated_rows}</strong><span>Обновится</span></article><article><strong>{batch.deactivated_rows}</strong><span>Деактивируется</span></article><article><strong>{batch.error_rows}</strong><span>Ошибок</span></article></div><p>Статус: <strong>{batch.status}</strong></p>{batch.error_rows === 0 && batch.status === "READY_TO_CONFIRM" && <button onClick={confirm}>Подтвердить импорт</button>}<button className="secondary" onClick={() => download(`/admin/imports/${batch.id}/errors.xlsx`, `import-${batch.id}-errors.xlsx`)}>Скачать отчёт</button></>}</section>;
}

export function StudentsPage() {
  const event = useEvent(); const [search, setSearch] = useState("");
  const query = useQuery({ queryKey: ["students", event.data?.id, search], enabled: Boolean(event.data), queryFn: () => api<{ items: Array<{ id: string; source_id: string; full_name: string; study_group: string; institute: string; is_active: boolean }> }>(`/admin/students?event_id=${event.data?.id}&search=${encodeURIComponent(search)}`) });
  return <section className="wide"><h1>Студенты</h1><label>Поиск<input value={search} onChange={e => setSearch(e.target.value)} placeholder="ФИО" /></label>{query.isLoading ? <Loading /> : <div className="table-wrap"><table><thead><tr><th>ID</th><th>ФИО</th><th>Группа</th><th>Институт</th><th>Активен</th></tr></thead><tbody>{query.data?.items.map(row => <tr key={row.id}><td>{row.source_id}</td><td>{row.full_name}</td><td>{row.study_group}</td><td>{row.institute}</td><td>{row.is_active ? "Да" : "Нет"}</td></tr>)}</tbody></table></div>}</section>;
}

export function UsersPage() {
  const client = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [createdCredentials, setCreatedCredentials] = useState<{ username: string; password: string } | null>(null);
  const [resetUserId, setResetUserId] = useState<string | null>(null);
  const [resetPassword, setResetPassword] = useState("");
  const query = useQuery({ queryKey: ["users"], queryFn: () => api<{ items: Array<{ id: string; username: string; role: string; is_active: boolean }> }>("/admin/users") });
  const mutation = useMutation({ mutationFn: (user: { id: string; is_active: boolean }) => api(`/admin/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !user.is_active }) }), onSuccess: () => client.invalidateQueries({ queryKey: ["users"] }) });
  const create = useMutation({
    mutationFn: (credentials: { username: string; password: string }) => api("/admin/users", { method: "POST", body: JSON.stringify({ ...credentials, role: "OPERATOR" }) }),
    onSuccess: (_, credentials) => {
      setCreatedCredentials(credentials);
      setUsername("");
      setPassword("");
      client.invalidateQueries({ queryKey: ["users"] });
    },
  });
  const reset = useMutation({
    mutationFn: ({ id, password: nextPassword }: { id: string; password: string }) => api(`/admin/users/${id}`, { method: "PATCH", body: JSON.stringify({ password: nextPassword }) }),
    onSuccess: () => {
      setResetUserId(null);
      setResetPassword("");
    },
  });
  return <section><h1>Операторы</h1><form autoComplete="off" onSubmit={event => { event.preventDefault(); setCreatedCredentials(null); create.mutate({ username: username.trim(), password }); }}><label>Логин<input autoComplete="off" value={username} onChange={event => setUsername(event.target.value)} /></label><label>Временный пароль<input type="password" autoComplete="new-password" spellCheck={false} value={password} minLength={12} onChange={event => setPassword(event.target.value)} /></label><button disabled={create.isPending}>Создать оператора</button>{create.error && <Status type="error">{errorMessage(create.error)}</Status>}</form>{createdCredentials && <Status type="success"><strong>Оператор создан. Сохраните данные сейчас — позже пароль посмотреть нельзя.</strong><br />Логин: <code>{createdCredentials.username}</code><br />Временный пароль: <code>{createdCredentials.password}</code></Status>}{query.isLoading ? <Loading /> : <ul className="list">{query.data?.items.map(user => <li key={user.id}><span><strong>{user.username}</strong><br />{user.role}</span><div className="operator-actions">{user.role === "OPERATOR" && <button className="secondary" onClick={() => { setResetUserId(user.id); setResetPassword(""); }}>Сбросить пароль</button>}<button className="secondary" onClick={() => mutation.mutate(user)}>{user.is_active ? "Отключить" : "Включить"}</button></div>{resetUserId === user.id && <form className="inline-reset" autoComplete="off" onSubmit={event => { event.preventDefault(); reset.mutate({ id: user.id, password: resetPassword }); }}><label>Новый временный пароль<input autoFocus type="password" autoComplete="new-password" spellCheck={false} minLength={12} value={resetPassword} onChange={event => setResetPassword(event.target.value)} /></label><button disabled={reset.isPending}>Сохранить пароль</button>{reset.error && <Status type="error">{errorMessage(reset.error)}</Status>}</form>}</li>)}</ul>}</section>;
}

export function AdminSchedulePage() {
  const event = useEvent(); const client = useQueryClient();
  const [form, setForm] = useState({ title: "", location: "", starts_at: "", ends_at: "" });
  const query = useQuery({ queryKey: ["admin-schedule", event.data?.id], enabled: Boolean(event.data), queryFn: () => api<{ items: Array<{ id: string; title: string; location: string; starts_at: string; is_published: boolean }> }>(`/admin/schedule?event_id=${event.data?.id}`) });
  const create = useMutation({ mutationFn: () => api("/admin/schedule", { method: "POST", body: JSON.stringify({ event_id: event.data?.id, title: form.title, location: form.location, starts_at: new Date(form.starts_at).toISOString(), ends_at: new Date(form.ends_at).toISOString(), description: null, display_order: 0, is_published: true }) }), onSuccess: () => { setForm({ title: "", location: "", starts_at: "", ends_at: "" }); client.invalidateQueries({ queryKey: ["admin-schedule"] }); } });
  return <section><h1>Управление расписанием</h1><form onSubmit={e => { e.preventDefault(); create.mutate(); }}><label>Название<input required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label><label>Локация<input required value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} /></label><label>Начало<input required type="datetime-local" value={form.starts_at} onChange={e => setForm({ ...form, starts_at: e.target.value })} /></label><label>Окончание<input required type="datetime-local" value={form.ends_at} onChange={e => setForm({ ...form, ends_at: e.target.value })} /></label><button>Добавить и опубликовать</button></form>{query.isLoading ? <Loading /> : <ul className="list">{query.data?.items.map(item => <li key={item.id}><span><strong>{item.title}</strong><br />{item.location}</span><time>{new Date(item.starts_at).toLocaleString("ru-RU")}</time></li>)}</ul>}</section>;
}

export function AdminMapPage() {
  const event = useEvent(); const [file, setFile] = useState<File | null>(null); const [message, setMessage] = useState("");
  async function upload() { if (!file || !event.data) return; const body = new FormData(); body.append("event_id", event.data.id); body.append("file", file); try { await api("/admin/map", { method: "POST", body }); setMessage("Карта опубликована"); } catch (caught) { setMessage(errorMessage(caught)); } }
  return <section><h1>Карта мероприятия</h1><p>PNG/JPEG/WebP будет безопасно перекодирован сервером в WebP.</p><input aria-label="Файл карты" type="file" accept="image/png,image/jpeg,image/webp" onChange={e => setFile(e.target.files?.[0] ?? null)} /><button disabled={!file} onClick={upload}>Опубликовать карту</button>{message && <Status>{message}</Status>}</section>;
}
