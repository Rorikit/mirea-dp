import type { PropsWithChildren } from "react";

export function Status({ type = "info", children }: PropsWithChildren<{ type?: "info" | "error" | "success" }>) {
  return <div className={`status status-${type}`} role={type === "error" ? "alert" : "status"}>{children}</div>;
}

export function Loading() { return <div className="skeleton" aria-label="Загрузка"><span /><span /><span /></div>; }
export function Empty({ children }: PropsWithChildren) { return <div className="empty">{children}</div>; }

