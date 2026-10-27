"use client";

import { useRouter } from "next/navigation";

import { ResumeUploadForm } from "@/components/ResumeUploadForm";
import { SESSION_EXPIRED } from "@/lib/api";
import { analyzeResume, uploadResume } from "@/lib/resumes";
import { getAccessToken } from "@/lib/supabase/token";

export function ResumeUploadSection() {
  const router = useRouter();

  return (
    <ResumeUploadForm
      upload={async (file) => {
        const token = await getAccessToken();
        if (!token) {
          return { state: "error", message: SESSION_EXPIRED };
        }
        const uploaded = await uploadResume(token, file);
        if (uploaded.state === "error") {
          return uploaded;
        }
        // Logo depois do envio, a IA lê o currículo. Se falhar, o arquivo já está salvo.
        const analysis = await analyzeResume(token, uploaded.resume.id);
        return analysis.state === "ok"
          ? { ...uploaded, notice: `Currículo "${uploaded.resume.original_filename}" enviado e analisado!` }
          : {
              ...uploaded,
              notice:
                `Currículo enviado, mas a análise não deu certo: ${analysis.message} ` +
                'Use o botão "Analisar com IA" para tentar de novo.',
            };
      }}
      // Recarrega os dados da página para a lista mostrar o envio novo.
      onUploaded={() => router.refresh()}
    />
  );
}
