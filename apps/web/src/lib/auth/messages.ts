const MESSAGES: Record<string, string> = {
  invalid_credentials: "E-mail ou senha incorretos.",
  email_not_confirmed: "Confirme seu e-mail antes de entrar. Procure a mensagem na sua caixa de entrada.",
  user_already_exists: "Já existe uma conta com este e-mail. Tente entrar.",
  weak_password: "Senha fraca. Escolha uma senha mais longa e difícil de adivinhar.",
  email_address_invalid: "Este e-mail não é válido.",
  over_email_send_rate_limit: "Muitos e-mails enviados em pouco tempo. Aguarde alguns minutos.",
  over_request_rate_limit: "Muitas tentativas em pouco tempo. Aguarde alguns minutos.",
};

/** Traduz um erro do Supabase Auth para uma mensagem em português para a tela. */
export function authErrorMessage(error: { code?: string }): string {
  return (error.code && MESSAGES[error.code]) || "Não foi possível concluir. Tente de novo.";
}
