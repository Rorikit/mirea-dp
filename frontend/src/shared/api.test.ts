import { afterEach, describe, expect, it } from "vitest";

import { getStaffRole, setAuth, staffHome } from "./api";

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
