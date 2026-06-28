const TOKEN_COOKIE = 'auth_token';
const ROLE_COOKIE = 'auth_role';
const MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export function setAuthCookies(token: string, role?: string | null) {
  if (typeof document === 'undefined') return;
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${MAX_AGE_SECONDS}; SameSite=Lax`;
  if (role) {
    document.cookie = `${ROLE_COOKIE}=${encodeURIComponent(role)}; path=/; max-age=${MAX_AGE_SECONDS}; SameSite=Lax`;
  }
}

export function clearAuthCookies() {
  if (typeof document === 'undefined') return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
  document.cookie = `${ROLE_COOKIE}=; path=/; max-age=0`;
}

export { TOKEN_COOKIE, ROLE_COOKIE };
