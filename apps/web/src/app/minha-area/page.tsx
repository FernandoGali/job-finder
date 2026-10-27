import { redirect } from "next/navigation";

import { SignOutButton } from "@/components/SignOutButton";
import { LOGIN_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/server";

export default async function MinhaAreaPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  if (!data.user) {
    redirect(LOGIN_PATH);
  }

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <h1>Minha área</h1>
      <p>Você entrou como {data.user.email}.</p>
      <SignOutButton />
    </main>
  );
}
