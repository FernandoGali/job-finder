import { redirect } from "next/navigation";

import { ConfirmEmailForm } from "@/components/ConfirmEmailForm";
import { parseConfirmParams } from "@/lib/auth/confirm";
import { LINK_ERROR_PATH } from "@/lib/auth/routes";

import { confirmEmail } from "./actions";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/** Destino do link do e-mail. Só mostra o botão: abrir a página não confirma nada. */
export default async function ConfirmarPage({ searchParams }: Props) {
  const params = parseConfirmParams(await searchParams);
  if (!params) {
    redirect(LINK_ERROR_PATH);
  }

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <ConfirmEmailForm params={params} action={confirmEmail} />
    </main>
  );
}
