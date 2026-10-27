"use client";

import { useRouter } from "next/navigation";

import { DeleteAccountSection } from "@/components/DeleteAccountSection";
import { callApi, SESSION_EXPIRED } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { getAccessToken } from "@/lib/supabase/token";

export function DeleteAccount() {
  const router = useRouter();

  return (
    <DeleteAccountSection
      deleteAccount={async () => {
        const token = await getAccessToken();
        return token ? callApi("DELETE", "/conta", token) : { state: "error", message: SESSION_EXPIRED };
      }}
      onDeleted={async () => {
        // A conta já não existe no Supabase; só limpa a sessão guardada neste navegador.
        await createClient().auth.signOut({ scope: "local" });
        router.replace("/?conta=excluida");
        router.refresh();
      }}
    />
  );
}
