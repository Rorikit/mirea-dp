import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Empty, Status } from "./ui";

describe("компоненты состояний", () => {
  it("показывает доступную ошибку", () => {
    render(<Status type="error">Ошибка соединения</Status>);
    expect(screen.getByRole("alert")).toHaveTextContent("Ошибка соединения");
  });

  it("показывает пустое состояние", () => {
    render(<Empty>Данных пока нет</Empty>);
    expect(screen.getByText("Данных пока нет")).toBeVisible();
  });
});

