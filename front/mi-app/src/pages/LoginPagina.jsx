import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import Boton from '../components/Boton';
import CampoTexto from '../components/CampoTexto';
import { useAuth } from '../context/useAuth';

export default function LoginPagina() {
  const { user, login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setEnviando(true);
    try {
      await login(username.trim(), password);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (loginError) {
      setError(loginError.message || 'No se pudo iniciar sesión');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main style={{ maxWidth: 420, margin: '12vh auto', padding: 24 }}>
      <h1 style={{ fontSize: 30, marginBottom: 8 }}>Rentar</h1>
      <p style={{ marginBottom: 24 }}>Ingresá con tu cuenta para continuar.</p>
      <form onSubmit={handleSubmit}>
        <CampoTexto
          label="Usuario"
          name="username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
        <CampoTexto
          label="Contraseña"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && <p role="alert" style={{ color: '#b42318', marginBottom: 16 }}>{error}</p>}
        <Boton type="submit" disabled={enviando}>
          {enviando ? 'Ingresando...' : 'Iniciar sesión'}
        </Boton>
      </form>
    </main>
  );
}