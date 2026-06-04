import { NextRequest, NextResponse } from 'next/server';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

export async function POST(request: NextRequest) {
  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.json(
      { error: 'SUPABASE_SERVICE_KEY and NEXT_PUBLIC_SUPABASE_URL must be configured.' },
      { status: 500 },
    );
  }

  const body = await request.json().catch(() => null);
  const userId = body?.user_id as string | undefined;

  if (!userId) {
    return NextResponse.json({ error: 'user_id is required.' }, { status: 400 });
  }

  // Validate that userId is a valid UUID to prevent injection
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(userId)) {
    return NextResponse.json({ error: 'Invalid user_id format. Must be a valid UUID.' }, { status: 400 });
  }

  const response = await fetch(
    `${supabaseUrl}/rest/v1/subscriptions?select=status,current_period_end&user_id=eq.${encodeURIComponent(userId)}&status=eq.active&limit=1`,
    {
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
        Accept: 'application/json',
      },
    },
  );

  if (!response.ok) {
    const text = await response.text();
    return NextResponse.json({ error: 'Failed to validate subscription.', details: text }, { status: 502 });
  }

  const subscriptions = await response.json();
  const activeSubscription = Array.isArray(subscriptions) && subscriptions.length > 0 ? subscriptions[0] : undefined;

  if (!activeSubscription) {
    return NextResponse.json({ error: 'No active subscription found for this user.' }, { status: 403 });
  }

  return NextResponse.json({
    message: 'License issuance endpoint configured. Implement JWT signing for production.',
    user_id: userId,
    subscription: activeSubscription,
  });
}
