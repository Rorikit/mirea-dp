import { afterEach, describe, expect, it } from "vitest";

import { getStaffRole, idempotencyKey, setAuth, staffHome } from "./api";

function token(role: string) {
  const payload = btoa(JSON.stringify({ role })).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `header.${payload}.signature`;
}

afterEach(() => setAuth(null));

describe("role-aware navigation", () => {
  it("routes an administrator to the admin dashboard", () => {
    setAuth(token("ADMIN"), "csrf");
    expect(getStaffRole()).toBe("ADMIN");
    expect(staffHome()).toBe("/admin");
  });

  it("routes an operator to the scanner", () => {
    setAuth(token("OPERATOR"), "csrf");
    expect(getStaffRole()).toBe("OPERATOR");
    expect(staffHome()).toBe("/operator/scanner");
  });
});

describe("idempotency keys", () => {
  it("creates UUID-shaped keys", () => {
    expect(idempotencyKey()).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });
});
