"use client";

import { useRouter } from "next/navigation";

import { ResumeUploadForm } from "@/components/ResumeUploadForm";
import { uploadResume } from "@/lib/resumes";
import { createClient } from "@/lib/supabase/client";

export function ResumeUploadSection() {
  const router = useRouter();

  return (
    <ResumeUploadForm
      upload={async (file) => {
        const { data } = await createClient().auth.getSession();
        const token = data.session?.access_token;
        if (!token) {
          return { state: "error", message: "Sua sessão expirou. Saia e entre de novo." };
        }
        return uploadResume(token, file);
      }}
      // Recarrega os dados da página para a lista mostrar o envio novo.
      onUploaded={() => router.refresh()}
    />
  );
}
