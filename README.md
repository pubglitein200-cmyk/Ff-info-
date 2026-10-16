# LIGHTNESS FF INFO

Discord bot starter for Free Fire profile lookups. It displays only values returned by the API you configure; it does not fabricate profile data.

## Commands
- `!ff UID` — fetch profile.
- `!ffhelp` — list commands.
- `!ffsetup` — save current channel as this server's setup/announcement channel (Manage Server permission required).
- `!ffsetshow` — show saved channel.
- `!ffsetreset` — clear saved channel (Manage Server permission required).
- `!ffannounce UID` — post profile in the saved channel.

## Railway deployment
1. Upload these files to GitHub and deploy the repository on Railway.
2. Add private Railway Variables: `DISCORD_TOKEN`, `FF_API_URL`, and optionally `FF_API_KEY`, `FF_API_KEY_HEADER`, `FF_API_KEY_PREFIX`.
3. `FF_API_URL` must be a compatible provider endpoint containing `{uid}`. No unverified API is bundled; use the provider's documented endpoint and authentication. The placeholder domain in any example is not a real API.
4. Enable **Message Content Intent** in Discord Developer Portal.
5. Give the bot View Channels, Send Messages, Embed Links and Read Message History permissions.
6. Check Railway logs after deployment.

## Persistence and secrets
Setup is stored in `ff_config.json`. Railway local files can be lost on redeploy unless you attach a persistent volume and set `CONFIG_PATH` appropriately. Never commit Discord tokens or API keys to GitHub. If exposed, reset the token in the Developer Portal.
