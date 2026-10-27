import { redirect } from "next/navigation";

import { ResumeList } from "@/components/ResumeList";
import { SignOutButton } from "@/components/SignOutButton";
import { LOGIN_PATH } from "@/lib/auth/routes";
import { fetchResumes, type ResumesResult } from "@/lib/resumes";
import { createClient } from "@/lib/supabase/server";

import { ResumeUploadSection } from "./ResumeUploadSection";

export default async function MinhaAreaPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  if (!data.user) {
    redirect(LOGIN_PATH);
  }

  // O token vai para a API, que confere a assinatura por conta própria.
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token;
  const resumes: ResumesResult = token
    ? await fetchResumes(token)
    : { state: "error", message: "Sua sessão expirou. Saia e entre de novo." };

  return (
    <main
      style={{
        maxWidth: 640,
        margin: "64px auto",
        padding: "0 16px",
        fontFamily: "system-ui",
        display: "grid",
        gap: 24,
      }}
    >
      <header>
        <h1 style={{ marginBottom: 4 }}>Minha área</h1>
        <p style={{ margin: 0 }}>
          Você entrou como {data.user.email}. <SignOutButton />
        </p>
      </header>
      <ResumeList result={resumes} />
      <ResumeUploadSection />
    </main>
  );
}
