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

export function EntrarForm({ notice }: { notice?: string }) {
  const router = useRouter();

  return (
    <LoginForm
      auth={auth}
      notice={notice}
      onSignedIn={() => {
        router.replace(HOME_PATH);
        router.refresh();
      }}
    />
  );
}
