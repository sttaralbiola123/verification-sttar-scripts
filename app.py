import os
import requests
import asyncio
import threading
from flask import Flask, render_template, redirect, session, request
from dotenv import load_dotenv
from bot import bot, verify_member
from database import init_db, save_user

load_dotenv()
init_db()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

API_ENDPOINT = 'https://discord.com/api/v10'
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

def run_bot():
    asyncio.run(bot.start(os.getenv('BOT_TOKEN')))

threading.Thread(target=run_bot, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    guild_id = request.args.get('guild_id')
    if guild_id:
        session['target_guild'] = guild_id
    scope = "identify guilds.join"
    url = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={scope.replace(' ','%20')}"
    return redirect(url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/failed')

    data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI}
    token_resp = requests.post(f'{API_ENDPOINT}/oauth2/token', data=data, auth=(CLIENT_ID, CLIENT_SECRET))

    if token_resp.status_code != 200:
        return redirect('/failed')

    access_token = token_resp.json()['access_token']
    user_resp = requests.get(f'{API_ENDPOINT}/users/@me', headers={'Authorization': f'Bearer {access_token}'})
    user = user_resp.json()

    discord_id = user['id']
    guild_id = session.get('target_guild')

    if guild_id:
        save_user(discord_id, guild_id, access_token)
        asyncio.run_coroutine_threadsafe(verify_member(discord_id, guild_id), bot.loop)

    session['user_id'] = discord_id
    session['username'] = user.get('global_name') or user['username']
    return redirect('/success')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/failed')
def failed():
    return render_template('failed.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
