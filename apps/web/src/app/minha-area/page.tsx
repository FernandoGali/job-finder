import { redirect } from "next/navigation";

import { ApiIdentity } from "@/components/ApiIdentity";
import { SignOutButton } from "@/components/SignOutButton";
import { fetchMe, type MeResult } from "@/lib/api";
import { LOGIN_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/server";

export default async function MinhaAreaPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  if (!data.user) {
    redirect(LOGIN_PATH);
  }

  // O token vai para a API, que confere a assinatura por conta própria.
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token;
  const apiResult: MeResult = token ? await fetchMe(token) : { state: "unauthorized" };

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <h1>Minha área</h1>
      <p>Você entrou como {data.user.email}.</p>
      <ApiIdentity result={apiResult} />
      <SignOutButton />
    </main>
  );
}
