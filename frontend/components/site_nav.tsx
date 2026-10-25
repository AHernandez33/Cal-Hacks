import Link from "next/link";

export default function SiteNav() {
  return (
    <nav className="navigation" aria-label="Main">
      <Link href="/">
        VigiloForge <span className="status-dot" aria-hidden="true" />
      </Link>
      <div className="actions">
        <Link href="/#dashboard">Dashboard</Link>
        <Link href="/greenhouses">Six greenhouse scenarios</Link>
        <Link href="/federated">Learning models</Link>
        <Link href="/research">Research</Link>
        <Link href="/field">Field Mode</Link>
        <Link href="/plans">Plans</Link>
        <Link href="/login">Workspace / sign in</Link>
      </div>
    </nav>
  );
}
