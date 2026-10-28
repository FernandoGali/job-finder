import { redirect } from "next/navigation";

import { ResetPasswordForm } from "@/components/ResetPasswordForm";
import { parseRecoveryLink } from "@/lib/auth/confirm";
import { RESET_LINK_ERROR_PATH } from "@/lib/auth/routes";

import { resetPassword } from "./actions";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/** Destino do link de redefinição. Abrir a página não muda nada; a troca é no envio. */
export default async function RedefinirSenhaPage({ searchParams }: Props) {
  const link = parseRecoveryLink(await searchParams);
  if (!link) {
    redirect(RESET_LINK_ERROR_PATH);
  }

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <ResetPasswordForm link={link} action={resetPassword} />
    </main>
  );
}
