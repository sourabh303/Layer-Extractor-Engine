import { createClient } from '../utils/supabase/server';
import { cookies } from 'next/headers';
import AuthForm from './components/AuthForm';
import SignOutButton from './components/SignOutButton';

export default async function Page() {
  const cookieStore = await cookies();
  const supabase = createClient(cookieStore);

  const { data: sessionData } = await supabase.auth.getSession();
  const user = sessionData?.session?.user;

  if (!user) {
    return (
      <main style={{ padding: 32, fontFamily: 'Inter, sans-serif' }}>
        <h1>Welcome to the Web Portal</h1>
        <p>Sign in or create an account to view your portal content.</p>
        <AuthForm />
      </main>
    );
  }

  const { data: todos, error } = await supabase.from('todos').select('*');

  return (
    <main style={{ padding: 32, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1>Portal Dashboard</h1>
          <p>Signed in as {user.email}</p>
        </div>
        <SignOutButton />
      </div>

      <section>
        <h2>Todo list</h2>
        {error ? (
          <p style={{ color: 'red' }}>Unable to load todos: {error.message}</p>
        ) : todos?.length ? (
          <ul>
            {todos.map((todo: { id: string; name: string }) => (
              <li key={todo.id}>{todo.name}</li>
            ))}
          </ul>
        ) : (
          <p>No todo items found.</p>
        )}
      </section>
    </main>
  );
}
