import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { NextRequest } from 'next/server';

// Need to mock fetch
const globalFetchMock = vi.fn();
global.fetch = globalFetchMock;

describe('POST /api/license/issue', () => {
  const ORIGINAL_ENV = process.env;
  let POST: any;

  beforeEach(async () => {
    vi.resetModules();
    process.env = { ...ORIGINAL_ENV };
    // Set default valid env vars for most tests
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://example.supabase.co';
    process.env.SUPABASE_SERVICE_KEY = 'test-service-key';
    globalFetchMock.mockReset();

    // Dynamically import the module so it picks up the current process.env
    const mod = await import('../../../../app/api/license/issue/route');
    POST = mod.POST;
  });

  afterEach(() => {
    process.env = ORIGINAL_ENV;
  });

  const createMockRequest = (body: any) => {
    return new NextRequest('http://localhost:3000/api/license/issue', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  };

  const createMockRequestInvalidBody = () => {
    return {
      json: () => Promise.reject(new Error('Invalid JSON')),
    } as unknown as NextRequest;
  };

  it('should return 500 if SUPABASE_SERVICE_KEY or NEXT_PUBLIC_SUPABASE_URL is missing', async () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    vi.resetModules(); // Force re-import to pick up missing env
    const mod = await import('../../../../app/api/license/issue/route');
    const POST_missing_env = mod.POST;

    const req = createMockRequest({ user_id: '123' });
    const res = await POST_missing_env(req);
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.error).toBe('SUPABASE_SERVICE_KEY and NEXT_PUBLIC_SUPABASE_URL must be configured.');
  });

  it('should return 400 if user_id is missing', async () => {
    const req = createMockRequest({});
    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe('user_id is required.');
  });

  it('should return 400 if user_id is missing (invalid JSON body)', async () => {
    const req = createMockRequestInvalidBody();
    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe('user_id is required.');
  });

  it('should return 400 if user_id is an invalid UUID format', async () => {
    const req = createMockRequest({ user_id: 'not-a-uuid' });
    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe('Invalid user_id format. Must be a valid UUID.');
  });

  it('should return 502 if Supabase response is not ok', async () => {
    globalFetchMock.mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Supabase Error'),
    });

    const validUuid = '123e4567-e89b-12d3-a456-426614174000';
    const req = createMockRequest({ user_id: validUuid });
    const res = await POST(req);
    expect(res.status).toBe(502);
    const data = await res.json();
    expect(data.error).toBe('Failed to validate subscription.');
    expect(data.details).toBe('Supabase Error');
  });

  it('should return 403 if no active subscription found (empty array)', async () => {
    globalFetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    const validUuid = '123e4567-e89b-12d3-a456-426614174000';
    const req = createMockRequest({ user_id: validUuid });
    const res = await POST(req);
    expect(res.status).toBe(403);
    const data = await res.json();
    expect(data.error).toBe('No active subscription found for this user.');
  });

  it('should return 403 if no active subscription found (not an array)', async () => {
    globalFetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ error: 'not an array' }),
    });

    const validUuid = '123e4567-e89b-12d3-a456-426614174000';
    const req = createMockRequest({ user_id: validUuid });
    const res = await POST(req);
    expect(res.status).toBe(403);
    const data = await res.json();
    expect(data.error).toBe('No active subscription found for this user.');
  });

  it('should return 200 with subscription info on success', async () => {
    const mockSubscription = { status: 'active', current_period_end: '2025-12-31' };
    globalFetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([mockSubscription]),
    });

    const validUuid = '123e4567-e89b-12d3-a456-426614174000';
    const req = createMockRequest({ user_id: validUuid });
    const res = await POST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.message).toBe('License issuance endpoint configured. Implement JWT signing for production.');
    expect(data.user_id).toBe(validUuid);
    expect(data.subscription).toEqual(mockSubscription);

    // Verify fetch was called with correct parameters
    expect(globalFetchMock).toHaveBeenCalledTimes(1);
    const urlCall = globalFetchMock.mock.calls[0][0];
    const fetchOptions = globalFetchMock.mock.calls[0][1];

    expect(urlCall).toContain('https://example.supabase.co/rest/v1/subscriptions');
    expect(urlCall).toContain(`user_id=eq.${encodeURIComponent(validUuid)}`);
    expect(urlCall).toContain('status=eq.active');
    expect(fetchOptions.headers.apikey).toBe('test-service-key');
    expect(fetchOptions.headers.Authorization).toBe('Bearer test-service-key');
  });
});
