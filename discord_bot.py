import discord
from discord.ext import commands
import asyncio
import matplotlib.pyplot as plt
import io
from datetime import datetime
from config import Config
from utils.helpers import setup_logger, format_number

logger = setup_logger(__name__)

class TradingBotNotifier:
    def __init__(self):
        self.token = Config.DISCORD_BOT_TOKEN
        self.channel_id = int(Config.DISCORD_CHANNEL_ID) if Config.DISCORD_CHANNEL_ID else None
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.channel = None
        self.is_ready = False
        
        @self.bot.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.bot.user}')
            if self.channel_id:
                self.channel = self.bot.get_channel(self.channel_id)
                if self.channel:
                    self.is_ready = True
                    await self.send_message("🤖 Trading Bot is now online and monitoring markets!")
                else:
                    logger.error(f"Could not find channel with ID: {self.channel_id}")
            else:
                logger.warning("No Discord channel ID configured")
        
        @self.bot.command(name='status')
        async def status(ctx):
            await ctx.send("✅ Trading bot is running!")
        
        @self.bot.command(name='balance')
        async def balance(ctx):
            await ctx.send("Use the dashboard to check your current balance.")
    
    async def start_bot(self):
        if not self.token:
            logger.warning("Discord bot token not configured. Notifications disabled.")
            return
        
        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
    
    async def send_message(self, message):
        if not self.is_ready or not self.channel:
            logger.warning("Discord bot not ready or channel not set")
            return
        
        try:
            await self.channel.send(message)
            logger.info(f"Sent Discord message: {message[:50]}...")
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
    
    async def send_trade_notification(self, trade_info):
        if not self.is_ready:
            return
        
        embed = discord.Embed(
            title=f"🔔 Trade Executed: {trade_info['symbol']}",
            color=discord.Color.green() if trade_info['type'] == 'BUY' else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Type", value=trade_info['type'], inline=True)
        embed.add_field(name="Price", value=f"${format_number(trade_info['price'])}", inline=True)
        embed.add_field(name="Quantity", value=format_number(trade_info['quantity'], 6), inline=True)
        
        if 'stop_loss' in trade_info:
            embed.add_field(name="Stop Loss", value=f"${format_number(trade_info['stop_loss'])}", inline=True)
        if 'take_profit' in trade_info:
            embed.add_field(name="Take Profit", value=f"${format_number(trade_info['take_profit'])}", inline=True)
        
        if 'reason' in trade_info:
            embed.add_field(name="Reason", value=trade_info['reason'], inline=False)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
    
    async def send_alert(self, alert_type, message):
        if not self.is_ready:
            return
        
        emoji = "⚠️" if alert_type == "warning" else "🚨"
        color = discord.Color.orange() if alert_type == "warning" else discord.Color.dark_red()
        
        embed = discord.Embed(
            title=f"{emoji} Alert: {alert_type.upper()}",
            description=message,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def send_performance_report(self, stats):
        if not self.is_ready:
            return
        
        embed = discord.Embed(
            title="📊 Daily Performance Report",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Account Balance", value=f"${format_number(stats['account_balance'])}", inline=True)
        embed.add_field(name="Total Trades", value=str(stats['total_trades']), inline=True)
        embed.add_field(name="Win Rate", value=f"{format_number(stats['win_rate'])}%", inline=True)
        embed.add_field(name="Total Profit", value=f"${format_number(stats['total_profit'])}", inline=True)
        embed.add_field(name="Max Drawdown", value=f"{format_number(stats['max_drawdown'])}%", inline=True)
        embed.add_field(name="ROI", value=f"{format_number(stats['roi'])}%", inline=True)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending performance report: {e}")
    
    async def close(self):
        if self.bot:
            await self.bot.close()
            logger.info("Discord bot closed")
