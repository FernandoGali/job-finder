import { NextResponse } from "next/server";

import { HOME_PATH, LINK_ERROR_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/server";

/** Destino do link de confirmação de e-mail: troca o código por uma sessão. */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${HOME_PATH}`);
    }
  }
  return NextResponse.redirect(`${origin}${LINK_ERROR_PATH}`);
}
