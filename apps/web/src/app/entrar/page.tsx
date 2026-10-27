import { EntrarForm } from "./EntrarForm";

const NOTICES: Record<string, string> = {
  link:
    "O link de confirmação não funcionou ou já foi usado. Se você já confirmou seu e-mail, é só " +
    "entrar. Se não, crie a conta de novo com o mesmo e-mail para receber outro link.",
};

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function EntrarPage({ searchParams }: Props) {
  const { erro } = await searchParams;
  const notice = typeof erro === "string" ? NOTICES[erro] : undefined;

  return (
    <main style={{ maxWidth: 640, margin: "64px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <EntrarForm notice={notice} />
    </main>
  );
}
