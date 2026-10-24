import OfflinePanel from "../../components/offline_panel";
import PWARegister from "../../components/pwa_register";
import Link from "next/link";
export default function OfflinePage() {
  return (
    <main className="container">
      <PWARegister />
      <h1>VigiloForge Field Mode</h1>
      <p>
        Previously saved photos remain on this device. Reconnect before server
        analysis or agent requests.
      </p>
      <OfflinePanel />
      <p>
        <Link href="/">Return to dashboard</Link>
      </p>
    </main>
  );
}
