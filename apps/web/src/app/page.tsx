import Link from "next/link";

import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { fetchApiStatus } from "@/lib/api";

export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function Home({ searchParams }: Props) {
  const status = await fetchApiStatus();
  const { conta } = await searchParams;

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      {conta === "excluida" && (
        <p role="status">Sua conta e todos os seus dados foram excluídos.</p>
      )}
      <h1>Job Finder</h1>
      <p>Suba seu currículo e receba as vagas que mais combinam com você.</p>
      <p>
        <Link href="/entrar">Entrar ou criar conta</Link>
      </p>
      <ApiStatusBadge status={status} />
    </main>
  );
}
