'use client';

import { createClient } from '../../utils/supabase/client';

export default function SignOutButton() {
  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.reload();
  };

  return (
    <button
      type="button"
      onClick={handleSignOut}
      style={{ padding: 10, borderRadius: 8, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}
    >
      Sign out
    </button>
  );
}
