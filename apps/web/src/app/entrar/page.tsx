"use client";

import { useRouter } from "next/navigation";

import { type AuthActions, LoginForm } from "@/components/LoginForm";
import { HOME_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/client";

// O cliente só é criado no clique: no build não existe .env nem navegador.
const auth: AuthActions = {
  signIn: (email, password) => createClient().auth.signInWithPassword({ email, password }),
  signUp: (email, password) =>
    createClient().auth.signUp({
      email,
      password,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    }),
};

export default function EntrarPage() {
  const router = useRouter();

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <LoginForm
        auth={auth}
        onSignedIn={() => {
          router.replace(HOME_PATH);
          router.refresh();
        }}
      />
    </main>
  );
}
