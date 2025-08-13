require('dotenv').config();
const { Telegraf } = require('telegraf');
const { Storage } = require('megajs');
const http = require('http');

const bot = new Telegraf(process.env.BOT_TOKEN);

let megaEmail = '';
let megaPass = '';
let megaStorage = null;

// ====== Mega Login ======
bot.command('setmega', async (ctx) => {
  const args = ctx.message.text.split(' ').slice(1);
  if (args.length < 2) return ctx.reply('Usage: /setmega <email> <password>');

  megaEmail = args[0];
  megaPass = args[1];

  try {
    megaStorage = new Storage({
      email: megaEmail,
      password: megaPass
    });

    megaStorage.on('ready', () => {
      ctx.reply(`Mega account set! Logged in as ${megaEmail}`);
    });
    megaStorage.on('error', (err) => ctx.reply(`Mega login error: ${err.message || err}`));
  } catch (err) {
    ctx.reply(`Login failed: ${err.message || err}`);
  }
});

// ====== Rename single file/folder ======
bot.command('rename_path', async (ctx) => {
  const args = ctx.message.text.split(' ').slice(1);
  if (args.length < 2) return ctx.reply('Usage: /rename_path <path> <new_name>');
  if (!megaStorage) return ctx.reply('⚠️ Set Mega account first using /setmega');

  const [path, ...nameParts] = args;
  const newName = nameParts.join(' ');

  try {
    const node = megaStorage.root.children.find(n => n.name === path || n._node.attributes.name === path);
    if (!node) return ctx.reply('File/folder not found');

    node.rename(newName, (err) => {
      if (err) return ctx.reply(`Rename failed: ${err.message || err}`);
      ctx.reply(`✅ Renamed: ${path} → ${newName}`);
    });
  } catch (e) {
    ctx.reply(`Error: ${e.message || e}`);
  }
});

// ====== Bulk rename (replace) ======
bot.command('rename_all', async (ctx) => {
  const args = ctx.message.text.split(' ').slice(1);
  if (args.length < 3) return ctx.reply('Usage: /rename_all replace <from> <to> [path]');
  if (!megaStorage) return ctx.reply('⚠️ Set Mega account first using /setmega');

  const mode = args[0].toLowerCase();
  if (mode !== 'replace') return ctx.reply('⚠️ Currently only replace mode is supported');

  const from = args[1];
  const to = args[2];
  const path = args[3] || '/';

  try {
    const folder = path === '/' ? megaStorage.root : megaStorage.root.children.find(n => n.name === path);
    if (!folder) return ctx.reply('Folder not found');

    const renameRecursive = async (node) => {
      for (const n of node.children || []) {
        let newName = n.name.replace(from, to);
        if (newName !== n.name) {
          await new Promise((res, rej) =>
            n.rename(newName, err => err ? rej(err) : res())
          );
          await ctx.reply(`✅ Renamed: ${n.name} → ${newName}`);
        }
        if (n.children) await renameRecursive(n);
      }
    };

    await renameRecursive(folder);
    ctx.reply('✅ Bulk rename completed!');
  } catch (e) {
    ctx.reply(`Error: ${e.message || e}`);
  }
});

// ====== Bot Start ======
bot.start((ctx) => ctx.reply('Welcome! Use /setmega <email> <pass> to login.'));

// Launch bot
bot.launch();
console.log('Bot is running...');

// ====== Render / PORT support ======
const port = process.env.PORT || 3000;
http.createServer((req, res) => res.end('Bot is running')).listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
