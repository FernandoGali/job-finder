"use server";

import { redirect } from "next/navigation";

import { parseConfirmParams } from "@/lib/auth/confirm";
import { HOME_PATH, LINK_ERROR_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/server";

/** Roda só quando a pessoa clica no botão; robôs que abrem o link não chegam aqui. */
export async function confirmEmail(formData: FormData) {
  const params = parseConfirmParams({
    token_hash: formData.get("token_hash"),
    type: formData.get("type"),
  });
  if (!params) {
    redirect(LINK_ERROR_PATH);
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.verifyOtp({
    token_hash: params.tokenHash,
    type: params.type,
  });
  redirect(error ? LINK_ERROR_PATH : HOME_PATH);
}
