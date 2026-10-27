// Mesma regra configurada no Supabase (Authentication → Email → senha):
// "Lowercase, uppercase letters and digits". Se mudar lá, mudar aqui.
export const PASSWORD_MIN_LENGTH = 8;

export type PasswordRule = {
  label: string;
  ok: (password: string) => boolean;
  problem: string;
};

// O Supabase só conta letras sem acento (a-z, A-Z).
export const PASSWORD_RULES: PasswordRule[] = [
  {
    label: `Mínimo de ${PASSWORD_MIN_LENGTH} caracteres;`,
    ok: (password) => password.length >= PASSWORD_MIN_LENGTH,
    problem: `A senha precisa ter pelo menos ${PASSWORD_MIN_LENGTH} caracteres.`,
  },
  {
    label: "Mínimo de 1 letra minúscula;",
    ok: (password) => /[a-z]/.test(password),
    problem: "A senha precisa ter pelo menos uma letra minúscula.",
  },
  {
    label: "Mínimo de 1 letra maiúscula;",
    ok: (password) => /[A-Z]/.test(password),
    problem: "A senha precisa ter pelo menos uma letra maiúscula.",
  },
  {
    label: "Mínimo de 1 número.",
    ok: (password) => /\d/.test(password),
    problem: "A senha precisa ter pelo menos um número.",
  },
];

/** Diz o que falta na senha para o cadastro, ou null se ela cumpre a regra. */
export function passwordProblem(password: string): string | null {
  return PASSWORD_RULES.find((rule) => !rule.ok(password))?.problem ?? null;
}
