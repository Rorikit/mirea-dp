import { expect, test } from "@playwright/test";

test("главная страница адаптирована для мобильного экрана", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "День первокурсника РТУ МИРЭА" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Получить QR-код" })).toBeVisible();
});
