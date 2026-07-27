import { BrowserQRCodeReader, type IScannerControls } from "@zxing/browser";
import { useEffect, useRef, useState } from "react";

export function CameraScanner({ onCode }: { onCode: (code: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const [error, setError] = useState("");
  const lastCode = useRef({ value: "", at: 0 });

  async function start() {
    setError("");
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError("Камера доступна только по HTTPS. Откройте https://168.222.202.190 и попробуйте снова.");
      return;
    }
    try {
      const reader = new BrowserQRCodeReader(undefined, { delayBetweenScanAttempts: 250 });
      controlsRef.current = await reader.decodeFromConstraints({ video: { facingMode: { ideal: "environment" } } }, videoRef.current!, (result) => {
        if (!result) return;
        const now = Date.now();
        if (result.getText() === lastCode.current.value && now - lastCode.current.at < 2000) return;
        lastCode.current = { value: result.getText(), at: now };
        onCode(result.getText());
      });
    } catch (reason) {
      const name = reason instanceof DOMException ? reason.name : "";
      if (name === "NotAllowedError") {
        setError("Доступ к камере запрещён. Разрешите камеру для этого сайта в настройках браузера.");
      } else if (name === "NotFoundError") {
        setError("Камера не найдена на устройстве.");
      } else if (name === "NotReadableError") {
        setError("Камера занята другим приложением или недоступна.");
      } else {
        setError("Не удалось получить доступ к камере. Разрешите доступ или используйте ручной ввод.");
      }
    }
  }

  function stop() { controlsRef.current?.stop(); controlsRef.current = null; }
  useEffect(() => stop, []);
  return <div className="scanner"><video ref={videoRef} muted playsInline /><div className="actions"><button onClick={start}>Включить камеру</button><button className="secondary" onClick={stop}>Остановить</button></div>{error && <p className="field-error" role="alert">{error}</p>}</div>;
}
