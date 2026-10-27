"use client";

import { useRouter } from "next/navigation";

import { ResumeUploadForm } from "@/components/ResumeUploadForm";
import { SESSION_EXPIRED } from "@/lib/api";
import { uploadResume } from "@/lib/resumes";
import { getAccessToken } from "@/lib/supabase/token";

export function ResumeUploadSection() {
  const router = useRouter();

  return (
    <ResumeUploadForm
      upload={async (file) => {
        const token = await getAccessToken();
        return token ? uploadResume(token, file) : { state: "error", message: SESSION_EXPIRED };
      }}
      // Recarrega os dados da página para a lista mostrar o envio novo.
      onUploaded={() => router.refresh()}
    />
  );
}
