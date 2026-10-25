import OfflinePanel from "../../components/offline_panel";
import PWARegister from "../../components/pwa_register";
export default function FieldPage() {
  return (
    <main className="container route-page">
      <PWARegister />
      <p className="eyebrow">Mobile observations</p>
      <h1>Field Mode</h1>
      <p className="hero-copy">
        Capture and save observations on this device, then choose when to send
        them. Open this page online once before using it offline.
      </p>
      <OfflinePanel />
    </main>
  );
}
