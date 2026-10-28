import { ForgotPasswordFormSection } from "./ForgotPasswordFormSection";

const NOTICES: Record<string, string> = {
  link: "O link para redefinir a senha não funcionou ou já foi usado. Peça um novo abaixo.",
};

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function EsqueciSenhaPage({ searchParams }: Props) {
  const { erro } = await searchParams;
  const notice = typeof erro === "string" ? NOTICES[erro] : undefined;

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <ForgotPasswordFormSection notice={notice} />
    </main>
  );
}
