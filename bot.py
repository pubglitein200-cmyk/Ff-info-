import os, json
from pathlib import Path
from typing import Any, Dict
import aiohttp
import discord
from discord.ext import commands

TOKEN=os.getenv('DISCORD_TOKEN','').strip()
API_URL=os.getenv('FF_API_URL','').strip()
API_KEY=os.getenv('FF_API_KEY','').strip()
API_HEADER=os.getenv('FF_API_KEY_HEADER','Authorization').strip() or 'Authorization'
API_PREFIX=os.getenv('FF_API_KEY_PREFIX','Bearer ')
CONFIG=Path(os.getenv('CONFIG_PATH','ff_config.json'))
intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix='!', intents=intents, help_command=None)
configs={}

def load():
    global configs
    try:
        configs=json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}
        if not isinstance(configs,dict): configs={}
    except (OSError,json.JSONDecodeError): configs={}
def save(): CONFIG.write_text(json.dumps(configs,indent=2),encoding='utf-8')
def cfg(gid): return configs.setdefault(str(gid),{})
def can_manage(ctx): return bool(ctx.guild and isinstance(ctx.author,discord.Member) and ctx.author.guild_permissions.manage_guild)
async def profile(uid):
    if not API_URL: raise RuntimeError('FF_API_URL is not configured in Railway Variables.')
    if not uid.isdigit(): raise ValueError('UID must contain digits only.')
    if '{uid}' not in API_URL: raise RuntimeError('FF_API_URL must contain {uid}.')
    headers={'Accept':'application/json','User-Agent':'LIGHTNESS-FF-INFO/1.0'}
    if API_KEY: headers[API_HEADER]=API_PREFIX+API_KEY
    timeout=aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout,headers=headers) as s:
        async with s.get(API_URL.replace('{uid}',uid)) as r:
            if r.status in (401,403): raise RuntimeError('API rejected the key/access. Check provider settings.')
            if r.status==404: raise LookupError('API did not find this UID.')
            if r.status==429: raise RuntimeError('API rate limit reached; try later.')
            if r.status>=400: raise RuntimeError(f'API returned HTTP {r.status}. Check endpoint/provider docs.')
            try: data=await r.json(content_type=None)
            except Exception as e: raise RuntimeError('API response was not valid JSON.') from e
    if not isinstance(data,dict): raise RuntimeError('Unexpected API response format.')
    for k in ('data','player','profile','result','account'):
        if isinstance(data.get(k),dict): data=data[k]; break
    return data
def get(d,*keys):
    for k in keys:
        if d.get(k) is not None and str(d[k]).strip(): return d[k]
    return None
def val(x): return 'Not provided by API' if x is None else (json.dumps(x,ensure_ascii=False)[:900] if isinstance(x,(dict,list)) else str(x)[:900])
def embed(uid,d):
    e=discord.Embed(title='LIGHTNESS FF INFO',description='**Nickname:** '+val(get(d,'nickname','name','playerName','player_name','nickName')),color=discord.Color.from_rgb(105,75,255))
    e.add_field(name='UID',value=uid,inline=True)
    for label,keys in [('Level',('level','playerLevel','player_level')),('EXP',('exp','experience','playerExp','player_exp')),('Likes',('likes','like','liked')),('Region',('region','server','country')),('Rank',('rank','rankPoints','rank_points','csRank','brRank'))]: e.add_field(name=label,value=val(get(d,*keys)),inline=True)
    e.add_field(name='Guild',value=val(get(d,'guild','guildName','guild_name','clan','clanName')),inline=False)
    e.set_footer(text='Only API-returned profile data is displayed.')
    return e

@bot.event
async def on_ready(): print(f'LIGHTNESS FF INFO logged in as {bot.user} ({bot.user.id})')
@bot.command(name='ff')
@commands.guild_only()
async def ff(ctx,uid:str=None):
    if not uid: return await ctx.reply('Use: `!ff UID`')
    try:
        async with ctx.typing(): d=await profile(uid.strip())
        await ctx.reply(embed=embed(uid.strip(),d),mention_author=False)
    except (ValueError,RuntimeError,LookupError) as e: await ctx.reply(f'**FF lookup failed:** {e}',mention_author=False)
    except aiohttp.ClientError: await ctx.reply('Could not connect to the API provider. Try again later.',mention_author=False)
@bot.command(name='ffhelp')
async def ffhelp(ctx):
    e=discord.Embed(title='LIGHTNESS FF INFO • Commands',description='`!ff UID` — look up profile\n`!ffhelp` — commands\n`!ffsetup` — set this channel (Manage Server)\n`!ffsetshow` — show saved channel\n`!ffsetreset` — reset setup (Manage Server)\n`!ffannounce UID` — publish profile in setup channel',color=discord.Color.from_rgb(105,75,255))
    e.set_footer(text='A compatible API is required; profile data is never fabricated.')
    await ctx.reply(embed=e,mention_author=False)
@bot.command(name='ffsetup')
@commands.guild_only()
async def ffsetup(ctx):
    if not can_manage(ctx): return await ctx.reply('Only members with **Manage Server** can configure this bot.')
    cfg(ctx.guild.id)['channel_id']=ctx.channel.id; save()
    await ctx.reply(f'Setup saved: {ctx.channel.mention}',mention_author=False)
@bot.command(name='ffsetshow')
@commands.guild_only()
async def ffsetshow(ctx):
    cid=cfg(ctx.guild.id).get('channel_id'); channel=ctx.guild.get_channel(int(cid)) if cid else None
    await ctx.reply(f'Setup channel: {channel.mention}' if channel else 'No valid setup channel. Run `!ffsetup` in the desired channel.',mention_author=False)
@bot.command(name='ffsetreset')
@commands.guild_only()
async def ffsetreset(ctx):
    if not can_manage(ctx): return await ctx.reply('Only members with **Manage Server** can reset setup.')
    configs.pop(str(ctx.guild.id),None); save(); await ctx.reply('Saved setup has been reset.',mention_author=False)
@bot.command(name='ffannounce')
@commands.guild_only()
async def ffannounce(ctx,uid:str=None):
    if not uid: return await ctx.reply('Use: `!ffannounce UID`')
    cid=cfg(ctx.guild.id).get('channel_id'); channel=ctx.guild.get_channel(int(cid)) if cid else None
    if not channel: return await ctx.reply('No setup channel. A member with **Manage Server** must run `!ffsetup` first.')
    try:
        async with ctx.typing(): d=await profile(uid.strip())
        await channel.send(embed=embed(uid.strip(),d)); await ctx.reply(f'Profile announcement sent to {channel.mention}.',mention_author=False)
    except (ValueError,RuntimeError,LookupError) as e: await ctx.reply(f'**Announcement failed:** {e}',mention_author=False)
    except aiohttp.ClientError: await ctx.reply('Could not connect to the API provider.',mention_author=False)
@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.CommandNotFound): return
    if isinstance(error,commands.NoPrivateMessage): return await ctx.reply('Use this command inside a server.')
    print('Command error:',repr(error)); await ctx.reply('Something went wrong. Check Railway logs.')
if __name__=='__main__':
    if not TOKEN: raise SystemExit('Missing DISCORD_TOKEN. Add it in Railway Variables.')
    load(); bot.run(TOKEN)
