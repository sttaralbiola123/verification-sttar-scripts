import sqlite3
from datetime import datetime

DB_PATH = 'data.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS guilds (
        guild_id TEXT PRIMARY KEY,
        verification_channel_id TEXT,
        not_verified_role_id TEXT,
        verified_role_id TEXT,
        setup_by TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        discord_id TEXT PRIMARY KEY,
        guild_id TEXT,
        access_token TEXT,
        verified INTEGER DEFAULT 0,
        verified_at TEXT
    )''')
    conn.commit()
    conn.close()

def save_guild(guild_id, channel_id, not_role, ver_role, setup_by):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO guilds VALUES (?,?,?,?,?)',
              (guild_id, channel_id, not_role, ver_role, setup_by))
    conn.commit()
    conn.close()

def get_guild(guild_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM guilds WHERE guild_id=?', (guild_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'guild_id': row[0],
            'verification_channel_id': row[1],
            'not_verified_role_id': row[2],
            'verified_role_id': row[3],
            'setup_by': row[4]
        }
    return None

def save_user(discord_id, guild_id, access_token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users (discord_id, guild_id, access_token, verified, verified_at) VALUES (?,?,?,1,?)',
              (discord_id, guild_id, access_token, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user(discord_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT access_token, guild_id FROM users WHERE discord_id=?', (discord_id,))
    row = c.fetchone()
    conn.close()
    return {'access_token': row[0], 'guild_id': row[1]} if row else None
