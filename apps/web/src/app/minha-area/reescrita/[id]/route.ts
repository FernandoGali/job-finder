import { SESSION_EXPIRED } from "@/lib/api";
import { DOCX, fetchRewriteDocx, REWRITE_DOCX_NAME } from "@/lib/resumes";
import { createClient } from "@/lib/supabase/server";

/** Download do currículo reescrito. Um link não manda o token, então o site busca o arquivo na
 * API com a sessão da pessoa e repassa. */
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    return new Response(SESSION_EXPIRED, { status: 401, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }

  const result = await fetchRewriteDocx(token, id);
  if (result.state === "error") {
    return new Response(result.message, { status: 502, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
  return new Response(result.file, {
    headers: {
      "Content-Type": DOCX,
      "Content-Disposition": `attachment; filename="${REWRITE_DOCX_NAME}"`,
    },
  });
}
