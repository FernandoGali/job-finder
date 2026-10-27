"use client";

import { useRouter } from "next/navigation";

import { LOGIN_PATH } from "@/lib/auth/routes";
import { createClient } from "@/lib/supabase/client";

export function SignOutButton() {
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={async () => {
        await createClient().auth.signOut();
        router.replace(LOGIN_PATH);
        router.refresh();
      }}
    >
      Sair
    </button>
  );
}
