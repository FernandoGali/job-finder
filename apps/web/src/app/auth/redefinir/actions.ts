"use server";

import { redirect } from "next/navigation";

import { parseConfirmParams, RECOVERY_TYPES } from "@/lib/auth/confirm";
import { authErrorMessage } from "@/lib/auth/messages";
import { passwordProblem } from "@/lib/auth/password";
import { HOME_PATH, RESET_LINK_ERROR_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/server";

export type ResetState = { error: string | null };

/**
 * Roda só no envio do formulário: robôs que abrem o link não gastam o código.
 * O código do link sempre vira a sessão (verifyOtp) antes da troca, mesmo que já haja alguém
 * logado no navegador: assim só a conta dona do link tem a senha trocada. Por isso a senha é
 * conferida antes, já que o código só vale uma vez.
 */
export async function resetPassword(_previous: ResetState, formData: FormData): Promise<ResetState> {
  const params = parseConfirmParams(
    { token_hash: formData.get("token_hash"), type: formData.get("type") },
    RECOVERY_TYPES,
  );
  if (!params) {
    redirect(RESET_LINK_ERROR_PATH);
  }

  const password = String(formData.get("password") ?? "");
  if (password !== String(formData.get("confirmation") ?? "")) {
    return { error: "As duas senhas não são iguais." };
  }
  const problem = passwordProblem(password);
  if (problem) {
    return { error: problem };
  }

  const supabase = await createClient();
  const verified = await supabase.auth.verifyOtp({ token_hash: params.tokenHash, type: "recovery" });
  if (verified.error) {
    redirect(RESET_LINK_ERROR_PATH);
  }

  const { error } = await supabase.auth.updateUser({ password });
  if (error) {
    return { error: authErrorMessage(error) };
  }
  redirect(HOME_PATH);
}
