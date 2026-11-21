import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const maxDuration = 900; // 15 minutes timeout to support full 9-image batch rendering

const BACKEND_BASE_URL = process.env.FASTAPI_BACKEND_URL || 'http://127.0.0.1:8000';

async function forwardRequest(req: NextRequest, { params }: { params: { path: string[] } }) {
  const subPath = (params.path || []).join('/');
  const targetUrl = new URL(`/api/v1/studio/${subPath}`, BACKEND_BASE_URL);

  // 转发所有 Query Parameters
  req.nextUrl.searchParams.forEach((val, key) => {
    targetUrl.searchParams.append(key, val);
  });

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    // 排除特定逐跳头部，让底层 fetch 自行管理
    if (!['host', 'connection', 'content-length'].includes(k)) {
      headers.set(key, value);
    }
  });

  try {
    let body: BodyInit | null = null;
    if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
      body = await req.arrayBuffer();
    }

    const initOptions: RequestInit = {
      method: req.method,
      headers,
      body,
    };

    // @ts-expect-error Node fetch supports duplex option for streaming
    initOptions.duplex = 'half';

    const backendRes = await fetch(targetUrl.toString(), initOptions);

    const contentType = backendRes.headers.get('content-type') || '';
    const isStream =
      contentType.includes('text/event-stream') ||
      contentType.includes('application/zip') ||
      contentType.includes('application/octet-stream');

    const responseHeaders = new Headers();
    backendRes.headers.forEach((val, key) => {
      const k = key.toLowerCase();
      if (!['transfer-encoding', 'content-encoding'].includes(k)) {
        responseHeaders.set(key, val);
      }
    });

    if (isStream) {
      return new Response(backendRes.body, {
        status: backendRes.status,
        headers: responseHeaders,
      });
    }

    const data = await backendRes.arrayBuffer();
    return new Response(data, {
      status: backendRes.status,
      headers: responseHeaders,
    });
  } catch (error: unknown) {
    const errorMsg = error instanceof Error ? error.message : '网络连接中断或服务未启动';
    console.error(`[Next.js API Gateway] Error forwarding to ${targetUrl}:`, error);
    return NextResponse.json(
      {
        detail: `后端服务 (FastAPI 端口 8000) 无法连接: ${errorMsg}。请确认后端服务已正常启动。`,
        success: false,
      },
      { status: 502 }
    );
  }
}

export const GET = forwardRequest;
export const POST = forwardRequest;
export const PUT = forwardRequest;
export const DELETE = forwardRequest;
export const PATCH = forwardRequest;
export const OPTIONS = forwardRequest;
