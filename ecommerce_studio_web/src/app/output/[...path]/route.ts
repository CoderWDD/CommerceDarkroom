export const dynamic = 'force-dynamic';

const BACKEND_BASE_URL = process.env.FASTAPI_BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(_req: Request, { params }: { params: { path: string[] } }) {
  const subPath = (params.path || []).join('/');
  const targetUrl = `${BACKEND_BASE_URL}/output/${subPath}`;

  try {
    const res = await fetch(targetUrl);
    if (!res.ok) {
      return new Response('Image not found', { status: res.status });
    }

    const contentType = res.headers.get('content-type') || 'image/jpeg';
    const data = await res.arrayBuffer();

    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch {
    return new Response('Error loading image', { status: 502 });
  }
}
