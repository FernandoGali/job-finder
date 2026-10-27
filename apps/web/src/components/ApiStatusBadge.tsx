import type { ApiStatus } from "@/lib/api";

export function ApiStatusBadge({ status }: { status: ApiStatus }) {
  if (status.state === "offline") {
    return (
      <p role="status" data-state="offline">
        API fora do ar ({status.reason})
      </p>
    );
  }

  const { version, env, supabase_configured } = status.health;
  return (
    <p role="status" data-state="online">
      API no ar · v{version} · {env} · Supabase{" "}
      {supabase_configured ? "configurado" : "ainda não configurado"}
    </p>
  );
}
