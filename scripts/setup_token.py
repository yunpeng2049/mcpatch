#!/usr/bin/env python3
"""Prompt for a token without echoing it; never pass secrets as CLI arguments."""
import getpass
import os
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / '.local'
    folder.mkdir(mode=0o700, exist_ok=True)
    os.chmod(folder, 0o700)
    token = getpass.getpass('粘贴麦当劳 MCP Token（输入不可见），然后回车：').strip()
    if not token or any(char.isspace() for char in token):
        raise SystemExit('Token 为空或含空白字符，未保存。请只复制 Token 本身。')
    target = folder / 'mcd_token'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as file:
        file.write(token)
    os.chmod(target, 0o600)
    print('Token 已保存至本项目 .local/mcd_token（仅当前用户可读写，Git 已忽略）。')
    print('可以回到聊天告诉助手：Token 已保存。请不要发送 Token 内容。')


if __name__ == '__main__':
    main()
