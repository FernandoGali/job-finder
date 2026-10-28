"use client";

import { ForgotPasswordForm } from "@/components/ForgotPasswordForm";
import { createClient } from "@/lib/supabase/client";

export function ForgotPasswordFormSection({ notice }: { notice?: string }) {
  return (
    <ForgotPasswordForm
      notice={notice}
      // O link do e-mail é montado pelo modelo "Reset Password" do Supabase
      // (/auth/redefinir?token_hash=...&type=recovery); o redirectTo fica de reserva.
      send={(email) =>
        createClient().auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/auth/redefinir`,
        })
      }
    />
  );
}
