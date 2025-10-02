#!/usr/bin/env python3
"""生成管理員密碼的 bcrypt hash"""

import bcrypt

passwords = {
    'admin123': None,
    'manager123': None
}

for password, _ in passwords.items():
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    passwords[password] = password_hash
    print(f"{password}: {password_hash}")
