export const LOGIN_PATH = "/entrar";
export const HOME_PATH = "/minha-area";
export const LINK_ERROR_PATH = `${LOGIN_PATH}?erro=link`;

const PROTECTED_PREFIXES = [HOME_PATH];

function matches(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

/** Para onde mandar a pessoa, ou null se ela pode ficar onde está. */
export function authRedirect(pathname: string, loggedIn: boolean): string | null {
  if (!loggedIn && PROTECTED_PREFIXES.some((prefix) => matches(pathname, prefix))) {
    return LOGIN_PATH;
  }
  if (loggedIn && matches(pathname, LOGIN_PATH)) {
    return HOME_PATH;
  }
  return null;
}
