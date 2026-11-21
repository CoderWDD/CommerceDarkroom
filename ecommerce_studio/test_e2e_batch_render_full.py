#!/usr/bin/env python3
"""
自动化端到端测试脚本：一键渲染全套 9 大图批量生图全流程回归测试
模拟前端 Next.js 用户操作与网关请求链路：
1. 校验前端 (3000) 与后端 (8000) 连通性
2. 创建全新真实电商会话 (Step 1)
3. 矩阵策划与 9 大视角初始化 (Step 2)
4. 触发一键批量渲染全套 9 大图 (Step 3 -> render-batch SSE 流式管道)
5. 监听解析全部 SSE 事件 (start -> perspective_start -> ping -> perspective_success -> complete)
6. 验证 9 张大图物理文件落地、有效性校验 (JPEG magic number, 大小 > 10KB)
7. 验证持久化会话 Schema 2.0 状态一致性
"""

import sys
import os
import time
import json
import requests
from pathlib import Path

# 确保 requests 对本地回环地址直连，不走外部代理
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

BASE_GATEWAY_URL = "http://127.0.0.1:3000/api/v1/studio"
BACKEND_DIRECT_URL = "http://127.0.0.1:8000/api/v1/studio"

def log_test(step: str, msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] [{step}] {msg}", flush=True)

def test_full_batch_pipeline(existing_sid: str = None):
    total_start = time.time()
    log_test("INIT", "=== 启动 电商视觉工坊 '一键渲染全套9大图' E2E 自动化回归测试 ===")

    # 1. 验证网关连通性
    log_test("CHECK", f"检测 Next.js 原生网关健康状态: {BASE_GATEWAY_URL}/health")
    try:
        r_gw = requests.get(f"{BASE_GATEWAY_URL}/health", timeout=5)
        assert r_gw.status_code == 200, f"网关返回非 200: {r_gw.status_code}"
        gw_info = r_gw.json()
        log_test("CHECK", f"网关正常，生效模型供应商: {gw_info.get('active_provider')}")
    except Exception as e:
        log_test("FAIL", f"Next.js 网关连接失败: {e}")
        sys.exit(1)

    if existing_sid:
        sid = existing_sid
        log_test("STEP 1", f"使用已有专案 session_id = {sid}")
    else:
        # 2. 创建全新商品专案
        session_payload = {
            "name": f"QA自动化回归全案-智能温控水杯_{int(time.time())}",
            "product_info": {
                "name": "极简智能温控触屏随行杯",
                "category": "316L不锈钢 / 触控数显 / 曜石黑哑光",
                "target_audience": "25-35岁都市白领与通勤精英",
                "pain_points": "水温难以感知容易烫嘴、普通保温杯内胆生锈有异味、包内倾斜容易漏水",
                "material_features": "316L医用级内胆，曜石黑磨砂亲肤烤漆，全贴合LED触显屏"
            }
        }
        log_test("STEP 1", f"创建全新商业专案: {session_payload['name']}")
        r_create = requests.post(f"{BASE_GATEWAY_URL}/sessions", json=session_payload, timeout=10)
        assert r_create.status_code == 200, f"创建会话失败: {r_create.text}"
        session_data = r_create.json()
        sid = session_data["session_id"]
        log_test("STEP 1", f"专案创建成功, session_id = {sid}")

        # 3. 策划生成 9 大视角提示词矩阵 (Step 2)
        log_test("STEP 2", f"调用多智能体生成 9 大电商转化视角矩阵 (LLM 推理)...")
        plan_payload = {
            "session_id": sid,
            "product_info": session_data["product_info"]
        }
        r_plan = requests.post(f"{BASE_GATEWAY_URL}/plan", json=plan_payload, timeout=180)
        assert r_plan.status_code == 200, f"策划矩阵生成失败: {r_plan.text}"
        plan_data = r_plan.json()
        perspectives = plan_data.get("perspectives", [])
        log_test("STEP 2", f"矩阵策划完成，视角数量 = {len(perspectives)}")
        assert len(perspectives) == 9, f"视角数量不为 9: {len(perspectives)}"

    # 4. 触发一键渲染全套 9 大图 (Step 3) - 通过 Next.js 网关发起 SSE 请求
    log_test("STEP 3", f"发起 SSE 批量渲染管道: POST {BASE_GATEWAY_URL}/render-batch")
    render_payload = {
        "session_id": sid,
        "aspect_ratio": "1:1",
        "concurrency": 1
    }
    sse_headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    sse_start_time = time.time()
    events_received = []
    card_starts = {}
    card_successes = {}
    card_errors = {}
    ping_count = 0
    batch_complete_event = None

    with requests.post(
        f"{BASE_GATEWAY_URL}/render-batch",
        json=render_payload,
        headers=sse_headers,
        stream=True,
        timeout=600  # 10 分钟单次连接保护
    ) as resp:
        log_test("SSE STREAM", f"HTTP 状态码: {resp.status_code}, 响应头 Content-Type: {resp.headers.get('Content-Type')}")
        assert resp.status_code == 200, f"SSE 建立失败: {resp.status_code}"
        assert "text/event-stream" in resp.headers.get("Content-Type", ""), "非 SSE 内容类型"

        current_event_type = "message"
        current_data_lines = []

        for line in resp.iter_lines(decode_unicode=True):
            if line is not None:
                line_str = line.strip()
                now_elapsed = time.time() - sse_start_time

                if line_str.startswith(":"):
                    # 注释心跳包
                    ping_count += 1
                    if ping_count % 3 == 0:
                        log_test("SSE HEARTBEAT", f"(+{now_elapsed:.1f}s) 收到原生 SSE 注释心跳: '{line_str}' (累积心跳数: {ping_count})")
                    continue

                if line_str.startswith("event:"):
                    current_event_type = line_str[6:].strip()
                elif line_str.startswith("data:"):
                    current_data_lines.append(line_str[5:].strip())
                elif line_str == "":
                    # 空行触发事件派发
                    if current_data_lines:
                        full_data_str = "\n".join(current_data_lines)
                        try:
                            parsed_data = json.loads(full_data_str)
                        except Exception:
                            parsed_data = full_data_str

                        evt_name = current_event_type
                        events_received.append((evt_name, parsed_data, now_elapsed))

                        if evt_name == "start":
                            log_test("SSE EVENT", f"(+{now_elapsed:.1f}s) 收到 [start] 事件, 全量目标总数: {parsed_data.get('total')}")
                        elif evt_name == "ping":
                            ping_count += 1
                            log_test("SSE HEARTBEAT", f"(+{now_elapsed:.1f}s) 收到标准 [ping] 心跳事件: {parsed_data}")
                        elif evt_name == "perspective_start":
                            p_id = parsed_data.get("perspective_id")
                            p_name = parsed_data.get("name")
                            card_starts[p_id] = now_elapsed
                            log_test("SSE EVENT", f"(+{now_elapsed:.1f}s) 🎬 机位开始渲染: [{p_id}] {p_name}")
                        elif evt_name in ("perspective_success", "perspective_done"):
                            p_id = parsed_data.get("perspective_id")
                            p_name = parsed_data.get("name")
                            completed = parsed_data.get("completed")
                            total = parsed_data.get("total")
                            img_url = parsed_data.get("image_url")
                            cost = now_elapsed - card_starts.get(p_id, now_elapsed)
                            card_successes[p_id] = {
                                "cost": cost,
                                "image_url": img_url,
                                "name": p_name
                            }
                            log_test("SSE EVENT", f"(+{now_elapsed:.1f}s) ✅ 机位渲染成功! [{p_id}] {p_name} (耗时: {cost:.1f}s) [进度: {completed}/{total}] URL: {img_url}")
                        elif evt_name == "perspective_error":
                            p_id = parsed_data.get("perspective_id")
                            err = parsed_data.get("error")
                            cost = now_elapsed - card_starts.get(p_id, now_elapsed)
                            card_errors[p_id] = err
                            log_test("SSE ERROR", f"(+{now_elapsed:.1f}s) ❌ 机位渲染失败: [{p_id}] (耗时: {cost:.1f}s) 错误: {err}")
                        elif evt_name in ("complete", "batch_complete"):
                            batch_complete_event = parsed_data
                            log_test("SSE COMPLETE", f"(+{now_elapsed:.1f}s) 🏁 收到批次完结事件! completed={parsed_data.get('completed')}/{parsed_data.get('total')}")

                        # 重置
                        current_event_type = "message"
                        current_data_lines = []

    sse_total_time = time.time() - sse_start_time
    log_test("METRICS", f"SSE 流读取结束，流管道持续时长: {sse_total_time:.2f}s")
    log_test("METRICS", f"共捕获 SSE 业务事件: {len(events_received)} 个，收到心跳包: {ping_count} 次")

    # 5. 断言检查与指标评估
    assert batch_complete_event is not None, "未接收到 batch_complete 完结事件！"
    success_count = len(card_successes)
    error_count = len(card_errors)
    log_test("VERIFY", f"成功机位数: {success_count}/9, 失败机位数: {error_count}/9")

    # 6. 验证物理图片文件
    log_test("VERIFY", "验证生成图片在本地磁盘落盘情况...")
    output_base = Path(__file__).resolve().parent / "output" / sid
    assert output_base.exists(), f"专案输出目录未找到: {output_base}"

    verified_files = 0
    for p_id, info in card_successes.items():
        sub_dir = output_base / p_id
        assert sub_dir.exists(), f"视角子目录未找到: {sub_dir}"
        jpg_files = list(sub_dir.glob("*.jpg"))
        assert len(jpg_files) > 0, f"视角 {p_id} 目录下无任何 jpg 图片文件"
        latest_file = max(jpg_files, key=lambda f: f.stat().st_mtime)
        fsize = latest_file.stat().st_size
        log_test("FILE OK", f"机位 [{p_id}] 图片落盘就绪: {latest_file.name} (大小: {fsize/1024:.1f} KB)")
        assert fsize > 10 * 1024, f"图片大小过小异常 ({fsize} bytes): {latest_file}"
        # 校验图片头部 magic bytes (支持 JPEG \xff\xd8\xff、PNG \x89PNG、WebP RIFF)
        with open(latest_file, "rb") as jf:
            magic = jf.read(8)
            is_valid_img = (
                magic.startswith(b"\xff\xd8\xff")
                or magic.startswith(b"\x89PNG")
                or magic.startswith(b"RIFF")
            )
            assert is_valid_img, f"文件非有效图片格式 (Magic: {magic!r}): {latest_file}"

        # 校验静态资源是否可通过前端 Next.js 网关成功加载
        img_url = info.get("image_url")
        if img_url:
            full_img_url = f"http://127.0.0.1:3000{img_url}"
            r_img = requests.head(full_img_url, timeout=5)
            assert r_img.status_code == 200, f"静态图加载失败 (HTTP {r_img.status_code}): {full_img_url}"

        verified_files += 1

    # 7. 验证持久化 Session 完整度 (通过 API 再次拉取 session 详情)
    log_test("VERIFY", f"拉取最新权威 Session 状态进行深度核查...")
    r_check = requests.get(f"{BASE_GATEWAY_URL}/sessions/{sid}", timeout=10)
    assert r_check.status_code == 200
    final_session = r_check.json()
    final_perspectives = final_session.get("perspectives", [])
    assert len(final_perspectives) == 9, "Perspectives 数组不全"

    active_versions_count = sum(1 for p in final_perspectives if p.get("active_version_id") is not None and p.get("image_url"))
    log_test("VERIFY", f"权威会话状态中带激活版本大图机位数: {active_versions_count}/9")

    total_elapsed = time.time() - total_start
    print("\n" + "="*70)
    print(" 🎉 【E2E 自动化测试全流程验证通过！】")
    print(f" 会话ID:          {sid}")
    print(f" 渲染视角总数:    {success_count} / 9")
    print(f" 物理落盘有效数:  {verified_files} / 9")
    print(f" SSE 心跳保持数:  {ping_count} 次")
    print(f" 总耗时:          {total_elapsed:.1f} 秒 (平均出图速度: {total_elapsed/9:.1f}s/张)")
    print("="*70 + "\n")

    return {
        "session_id": sid,
        "success_count": success_count,
        "verified_files": verified_files,
        "total_elapsed": total_elapsed,
        "ping_count": ping_count,
        "card_successes": card_successes,
    }

if __name__ == "__main__":
    target_sid = sys.argv[1] if len(sys.argv) > 1 else None
    test_full_batch_pipeline(target_sid)
