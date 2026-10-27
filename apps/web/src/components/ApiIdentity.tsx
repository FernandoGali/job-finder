import type { MeResult } from "@/lib/api";

/** Mostra se a API reconheceu a pessoa logada pelo token do Supabase. */
export function ApiIdentity({ result }: { result: MeResult }) {
  if (result.state === "ok") {
    return (
      <p role="status" data-state="ok">
        A API reconheceu você ({result.me.email}).
      </p>
    );
  }
  if (result.state === "unauthorized") {
    return (
      <p role="status" data-state="unauthorized">
        A API não reconheceu sua sessão. Saia e entre de novo.
      </p>
    );
  }
  return (
    <p role="status" data-state="offline">
      API fora do ar ({result.reason}).
    </p>
  );
}
