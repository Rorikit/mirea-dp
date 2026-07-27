import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { z } from "zod";
import { api, errorMessage, EVENT_SLUG } from "../shared/api";
import { Empty, Loading, Status } from "../shared/ui";

type Qr = { token: string; purpose: "ENTRY" | "EXIT"; expires_at: string };
type Profile = { public_id: string; full_name: string; study_group: string; institute: string; presence_status: "OUTSIDE" | "INSIDE"; qr?: Qr };
const registrationSchema = z.object({ full_name: z.string().min(2, "Введите ФИО"), study_group: z.string().min(2, "Введите группу") });
type RegistrationValues = z.infer<typeof registrationSchema>;

export function HomePage() {
  return <section className="hero"><p className="eyebrow">1 сентября 2026 · Москва</p><h1>День первокурсника РТУ МИРЭА</h1><p>Ваш QR-код для входа, расписание и карта мероприятия — в одном мобильном интерфейсе.</p><div className="actions"><Link className="button" to="/register">Получить QR-код</Link><Link className="button secondary" to="/schedule">Расписание</Link></div></section>;
}

function QrCard({ qr }: { qr: Qr }) {
  return <div className="qr-card"><p className="pill">{qr.purpose === "ENTRY" ? "Для входа" : "Для выхода"}</p><QRCodeSVG value={qr.token} size={260} marginSize={4} level="M" /><p>Действует до {new Date(qr.expires_at).toLocaleTimeString("ru-RU")}</p></div>;
}

export function RegisterPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegistrationValues>({ resolver: zodResolver(registrationSchema) });
  async function submit(values: RegistrationValues) {
    setError("");
    try {
      const lookup = await api<{ lookup_token: string }>("/public/registrations/lookup", { method: "POST", body: JSON.stringify({ event_slug: EVENT_SLUG, ...values }) });
      setProfile(await api<Profile>("/public/registrations", { method: "POST", body: JSON.stringify({ lookup_token: lookup.lookup_token }), headers: { "Idempotency-Key": crypto.randomUUID() } }));
    } catch (caught) { setError(errorMessage(caught)); }
  }
  if (profile?.qr) return <section><h1>Ваш QR-код готов</h1><Status type="success">Регистрация выполнена</Status><QrCard qr={profile.qr} /><Link className="button" to="/me">Открыть личный кабинет</Link></section>;
  return <section><h1>Регистрация</h1><p>Введите данные точно так, как они указаны в списках университета.</p><form onSubmit={handleSubmit(submit)}><label>ФИО<input autoComplete="name" {...register("full_name")} /></label>{errors.full_name && <span className="field-error">{errors.full_name.message}</span>}<label>Учебная группа<input autoCapitalize="characters" {...register("study_group")} /></label>{errors.study_group && <span className="field-error">{errors.study_group.message}</span>}{error && <Status type="error">{error}</Status>}<button disabled={isSubmitting}>{isSubmitting ? "Проверяем…" : "Получить QR-код"}</button></form></section>;
}

export function MePage() {
  const [qr, setQr] = useState<Qr | null>(null);
  const profile = useQuery({ queryKey: ["me"], queryFn: () => api<Profile>("/public/registrations/me") });
  async function createQr() { setQr(await api<Qr>("/public/registrations/me/qr", { method: "POST", body: JSON.stringify({ purpose: profile.data?.presence_status === "INSIDE" ? "EXIT" : "ENTRY" }), headers: { "Idempotency-Key": crypto.randomUUID() } })); }
  if (profile.isLoading) return <Loading />;
  if (profile.error) return <Status type="error">{errorMessage(profile.error)}</Status>;
  return <section><h1>Личный кабинет</h1><dl><dt>ФИО</dt><dd>{profile.data?.full_name}</dd><dt>Группа</dt><dd>{profile.data?.study_group}</dd><dt>Институт</dt><dd>{profile.data?.institute}</dd><dt>Статус</dt><dd>{profile.data?.presence_status === "INSIDE" ? "Вы находитесь на мероприятии" : "Вы можете войти"}</dd></dl>{qr ? <QrCard qr={qr} /> : <button onClick={createQr}>Показать новый QR-код</button>}</section>;
}

export function SchedulePage() {
  const query = useQuery({ queryKey: ["schedule"], queryFn: () => api<{ items: Array<{ id: string; title: string; location: string; starts_at: string; ends_at: string }> }>(`/public/schedule?event_slug=${EVENT_SLUG}`) });
  if (query.isLoading) return <Loading />;
  if (query.error) return <Status type="error">{errorMessage(query.error)}</Status>;
  return <section><h1>Расписание</h1>{query.data?.items.length ? <div className="timeline">{query.data.items.map(item => <article key={item.id}><time>{new Date(item.starts_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}</time><div><h2>{item.title}</h2><p>{item.location}</p></div></article>)}</div> : <Empty>Расписание пока не опубликовано</Empty>}</section>;
}

export function MapPage() {
  const query = useQuery({ queryKey: ["map"], queryFn: () => api<{ url: string }>(`/public/map?event_slug=${EVENT_SLUG}`), retry: false });
  if (query.isLoading) return <Loading />;
  if (query.error) return <Status type="error">{errorMessage(query.error)}</Status>;
  return <section><h1>Карта площадки</h1><div className="map-scroll"><img src={query.data?.url} alt="Карта площадки мероприятия" /></div></section>;
}
