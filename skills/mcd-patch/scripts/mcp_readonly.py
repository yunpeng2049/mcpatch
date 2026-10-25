#!/usr/bin/env python3
"""Small read-only Streamable HTTP MCP client for the official McDonald's host."""
import argparse
import json
import os
import socket
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler

URL = 'https://mcp.mcd.cn'
READ_ONLY = frozenset({
    'now-time-info', 'query-nearby-stores', 'delivery-query-addresses',
    'delivery-query-stores', 'query-meals', 'query-meal-detail',
    'query-store-coupons', 'calculate-price', 'list-nutrition-foods',
})


class MCPError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MCPError('服务器要求重定向；为避免凭证转发，已停止。')


def tls_context():
    """Some portable macOS Pythons point to a nonexistent build-time CA path."""
    paths = ssl.get_default_verify_paths()
    system_ca = Path('/etc/ssl/cert.pem')
    if (not paths.cafile and not paths.capath and
            not os.environ.get('SSL_CERT_FILE') and system_ca.is_file()):
        return ssl.create_default_context(cafile=str(system_ca))
    return ssl.create_default_context()


def load_token():
    token = os.environ.get('MCD_MCP_TOKEN', '').strip()
    if not token:
        override = os.environ.get('MCD_MCP_TOKEN_FILE')
        paths = [Path(override)] if override else [
            parent / '.local' / 'mcd_token' for parent in Path(__file__).resolve().parents
        ]
        for path in paths:
            if path.is_file():
                token = path.read_text(encoding='utf-8').strip()
                break
    if not token or any(c.isspace() for c in token):
        raise MCPError('未配置有效 Token。请运行项目 scripts/setup_token.py，或设置 MCD_MCP_TOKEN。')
    return token


def find_response(payload, request_id):
    messages = payload if isinstance(payload, list) else [payload]
    for message in messages:
        if isinstance(message, dict) and message.get('id') == request_id and (
            'result' in message or 'error' in message
        ):
            return message
    return None


def read_sse(response, request_id):
    parts, total = [], 0
    for line in response:
        total += len(line)
        if total > 8 * 1024 * 1024:
            raise MCPError('响应超过大小限制。')
        text = line.decode('utf-8').rstrip('\r\n')
        if text.startswith('data:'):
            parts.append(text[5:].lstrip(' '))
        elif not text and parts:
            message = find_response(json.loads('\n'.join(parts)), request_id)
            if message is not None:
                return message
            parts = []
    if parts:
        message = find_response(json.loads('\n'.join(parts)), request_id)
        if message is not None:
            return message
    raise MCPError('SSE 在收到匹配的结果前已结束。')


class Client:
    def __init__(self, token):
        self.token = token
        self.session = None
        self.protocol = '2025-03-26'
        self.counter = 0
        self.opener = build_opener(NoRedirect(), HTTPSHandler(context=tls_context()))

    def rpc(self, method, params=None, *, notification=False):
        body = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            body['params'] = params
        if not notification:
            self.counter += 1
            body['id'] = self.counter
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'MCP-Protocol-Version': self.protocol,
        }
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        request = Request(URL, json.dumps(body).encode('utf-8'), headers, method='POST')
        try:
            with self.opener.open(request, timeout=30) as response:
                self.session = response.headers.get('Mcp-Session-Id') or self.session
                if notification:
                    return None
                if 'text/event-stream' in response.headers.get('Content-Type', ''):
                    message = read_sse(response, body['id'])
                else:
                    raw = response.read(8 * 1024 * 1024 + 1)
                    if len(raw) > 8 * 1024 * 1024:
                        raise MCPError('响应超过大小限制。')
                    message = find_response(json.loads(raw), body['id'])
                if message is None:
                    raise MCPError('没有收到匹配的 JSON-RPC 响应。')
                if 'error' in message:
                    code = message['error'].get('code', 'unknown')
                    raise MCPError(f'MCP 协议错误 {code}；不输出可能包含隐私的原始错误体。')
                return message['result']
        except HTTPError as exc:
            hint = {401: 'Token 无效或过期', 403: '权限不足', 429: '请求受限，请稍后重试',
                    404: '会话或端点失效，请重新运行建立会话'}.get(exc.code, '请求失败')
            raise MCPError(f'HTTP {exc.code}：{hint}。') from None
        except (URLError, TimeoutError, socket.timeout, OSError):
            raise MCPError('网络或证书验证失败，未自动重试；请检查连接。') from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise MCPError('服务器响应不是预期的 JSON/SSE 格式。') from None

    def initialize(self):
        result = self.rpc('initialize', {
            'protocolVersion': self.protocol, 'capabilities': {},
            'clientInfo': {'name': 'mcpatch-readonly', 'version': '0.1.0'},
        })
        version = result.get('protocolVersion')
        if version not in ('2025-03-26', '2025-06-18', '2025-11-25'):
            raise MCPError('服务端协商的协议版本未受此客户端支持，请使用兼容的 MCP 宿主。')
        self.protocol = version
        self.rpc('notifications/initialized', notification=True)
        return result

    def list_tools(self):
        collected, cursor, seen = [], None, set()
        for _ in range(20):
            result = self.rpc('tools/list', {'cursor': cursor} if cursor else {})
            collected.extend(result.get('tools', []))
            cursor = result.get('nextCursor')
            if not cursor:
                return collected
            if cursor in seen:
                break
            seen.add(cursor)
        raise MCPError('工具列表分页异常，已停止。')

    def call(self, name, arguments, tool_list):
        if name not in READ_ONLY:
            raise MCPError('该工具不在本项目的只读允许列表中。')
        tool = next((t for t in tool_list if t.get('name') == name), None)
        if not tool:
            raise MCPError('当前服务器没有该工具；请检查 tools/list。')
        if not isinstance(arguments, dict):
            raise MCPError('arguments 必须是 JSON 对象。')
        required = tool.get('inputSchema', {}).get('required', [])
        missing = [name for name in required if name not in arguments]
        if missing:
            raise MCPError('缺少当前 schema 的必填参数：' + ', '.join(missing))
        result = self.rpc('tools/call', {'name': name, 'arguments': arguments})
        if result.get('isError'):
            raise MCPError('工具返回 isError；该调用不能视作查询或核价成功。')
        business = result.get('structuredContent')
        if isinstance(business, dict) and business.get('success') is False:
            raise MCPError('工具业务返回 success=false；该调用不能视作查询或核价成功。')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    call = commands.add_parser('call')
    call.add_argument('name', choices=sorted(READ_ONLY))
    group = call.add_mutually_exclusive_group()
    group.add_argument('--args', default='{}')
    group.add_argument('--args-file', type=Path)
    args = parser.parse_args()
    try:
        client = Client(load_token())
        client.initialize()
        tool_list = client.list_tools()
        if args.command == 'list':
            output = {'server': URL, 'tools': tool_list}
        else:
            raw = args.args_file.read_text(encoding='utf-8') if args.args_file else args.args
            output = client.call(args.name, json.loads(raw), tool_list)
        # A server should never echo credentials, but redact them if it does.
        print(json.dumps(output, ensure_ascii=False, indent=2).replace(client.token, '[REDACTED]'))
    except (MCPError, OSError, ValueError) as exc:
        # Avoid traceback / raw HTTP error bodies that may contain credentials.
        print(str(exc) if isinstance(exc, MCPError) else '本地参数/文件格式错误。', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
