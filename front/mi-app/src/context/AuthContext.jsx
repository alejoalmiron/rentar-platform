import { useEffect, useState } from 'react';
import { cerrarSesionApi, iniciarSesionApi } from '../service/ConectarAlBackend';
import { AuthContext } from './authContext';

function readStoredSession() {
  const token = localStorage.getItem('rentar.token');
  const storedUser = localStorage.getItem('rentar.user');
  if (!token || !storedUser) return null;

  try {
    return { token, user: JSON.parse(storedUser) };
  } catch {
    localStorage.removeItem('rentar.token');
    localStorage.removeItem('rentar.user');
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readStoredSession);

  useEffect(() => {
    function clearExpiredSession() {
      localStorage.removeItem('rentar.token');
      localStorage.removeItem('rentar.user');
      setSession(null);
    }

    window.addEventListener('rentar:unauthorized', clearExpiredSession);
    return () => window.removeEventListener('rentar:unauthorized', clearExpiredSession);
  }, []);

  async function login(username, password) {
    const result = await iniciarSesionApi({ username, password });
    const nextSession = { token: result.token, user: result.user };
    localStorage.setItem('rentar.token', result.token);
    localStorage.setItem('rentar.user', JSON.stringify(result.user));
    setSession(nextSession);
  }

  async function logout() {
    try {
      await cerrarSesionApi();
    } catch (error) {
      console.warn('No se pudo confirmar el cierre de sesión en el Gateway:', error.message);
    } finally {
      localStorage.removeItem('rentar.token');
      localStorage.removeItem('rentar.user');
      setSession(null);
    }
  }

  return (
    <AuthContext.Provider value={{
      token: session?.token || null,
      user: session?.user || null,
      login,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}