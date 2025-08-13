require('dotenv').config();
const { Telegraf } = require('telegraf');
const { Storage } = require('megajs');

const bot = new Telegraf(process.env.BOT_TOKEN);

let megaEmail = '';
let megaPass = '';

bot.start((ctx) => ctx.reply('Welcome! Use /setmega <email> <pass> to login.'));

bot.command('setmega', async (ctx) => {
  const args = ctx.message.text.split(' ').slice(1);
  if (args.length < 2) return ctx.reply('Usage: /setmega <email> <password>');
  megaEmail = args[0];
  megaPass = args[1];
  ctx.reply('Mega account set! Now you can rename files.');
});

bot.launch();
console.log('Bot is running...');
