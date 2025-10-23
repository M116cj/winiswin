import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from config import Config
from utils.helpers import setup_logger, format_number

logger = setup_logger(__name__)

class TradingBotNotifier:
    def __init__(self, risk_manager=None):
        self.token = Config.DISCORD_BOT_TOKEN
        self.channel_id = int(Config.DISCORD_CHANNEL_ID) if Config.DISCORD_CHANNEL_ID else None
        self.risk_manager = risk_manager  # 用於查詢倉位和餘額
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.channel = None
        self.is_ready = False
        
        # 設置命令
        self._setup_commands()
        
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
    
    def set_risk_manager(self, risk_manager):
        """設置 RiskManager 實例用於查詢"""
        self.risk_manager = risk_manager
    
    def _setup_commands(self):
        """設置所有 Discord 命令"""
        
        @self.bot.command(name='commands', help='顯示所有可用命令')
        async def commands_list(ctx):
            embed = discord.Embed(
                title="🤖 交易機器人命令列表",
                description="可用的命令：",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="!commands",
                value="顯示此命令列表",
                inline=False
            )
            embed.add_field(
                name="!positions",
                value="查看當前持倉",
                inline=False
            )
            embed.add_field(
                name="!balance",
                value="查看賬戶餘額和性能統計",
                inline=False
            )
            embed.add_field(
                name="!stats",
                value="查看詳細性能統計",
                inline=False
            )
            embed.add_field(
                name="!status",
                value="查看機器人運行狀態",
                inline=False
            )
            embed.add_field(
                name="!config",
                value="查看當前配置",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='positions', help='查看當前持倉')
        async def positions(ctx):
            if not self.risk_manager:
                await ctx.send("❌ 風險管理器未初始化")
                return
            
            open_positions = self.risk_manager.open_positions
            
            if not open_positions:
                embed = discord.Embed(
                    title="📊 當前持倉",
                    description="目前沒有持倉",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(
                    name="可用倉位",
                    value=f"{self.risk_manager.max_concurrent_positions}/3",
                    inline=True
                )
            else:
                embed = discord.Embed(
                    title="📊 當前持倉",
                    description=f"持倉數量: {len(open_positions)}/{self.risk_manager.max_concurrent_positions}",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                for symbol, pos in open_positions.items():
                    pnl = ((pos['current_price'] - pos['entry_price']) / pos['entry_price']) * 100 if pos['side'] == 'LONG' else ((pos['entry_price'] - pos['current_price']) / pos['entry_price']) * 100
                    pnl_emoji = "🟢" if pnl > 0 else "🔴"
                    
                    position_info = (
                        f"**方向**: {pos['side']}\n"
                        f"**入場**: ${format_number(pos['entry_price'])}\n"
                        f"**當前**: ${format_number(pos['current_price'])}\n"
                        f"**數量**: {format_number(pos['quantity'], 6)}\n"
                        f"**止損**: ${format_number(pos['stop_loss'])}\n"
                        f"**止盈**: ${format_number(pos['take_profit'])}\n"
                        f"**盈虧**: {pnl_emoji} {format_number(pnl)}%"
                    )
                    embed.add_field(name=f"📈 {symbol}", value=position_info, inline=True)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='balance', help='查看賬戶餘額')
        async def balance(ctx):
            if not self.risk_manager:
                await ctx.send("❌ 風險管理器未初始化")
                return
            
            stats = self.risk_manager.get_performance_stats()
            
            embed = discord.Embed(
                title="💰 賬戶資訊",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            # 餘額資訊
            embed.add_field(
                name="賬戶餘額",
                value=f"${format_number(stats['account_balance'])}",
                inline=True
            )
            embed.add_field(
                name="總盈虧",
                value=f"${format_number(stats['total_profit'])}",
                inline=True
            )
            embed.add_field(
                name="投資回報率",
                value=f"{format_number(stats['roi'])}%",
                inline=True
            )
            
            # 倉位資訊
            open_positions = len(self.risk_manager.open_positions)
            embed.add_field(
                name="當前倉位",
                value=f"{open_positions}/{self.risk_manager.max_concurrent_positions}",
                inline=True
            )
            embed.add_field(
                name="可用倉位",
                value=f"{self.risk_manager.max_concurrent_positions - open_positions}",
                inline=True
            )
            
            # 資金分配
            capital_per_position = stats['account_balance'] / 3
            embed.add_field(
                name="每倉位資金",
                value=f"${format_number(capital_per_position)}",
                inline=True
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='stats', help='查看詳細統計')
        async def stats(ctx):
            if not self.risk_manager:
                await ctx.send("❌ 風險管理器未初始化")
                return
            
            stats = self.risk_manager.get_performance_stats()
            
            embed = discord.Embed(
                title="📊 詳細性能統計",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # 交易統計
            embed.add_field(name="總交易數", value=str(stats['total_trades']), inline=True)
            embed.add_field(name="勝率", value=f"{format_number(stats['win_rate'])}%", inline=True)
            embed.add_field(name="最大回撤", value=f"{format_number(stats['max_drawdown'])}%", inline=True)
            
            embed.add_field(name="贏的交易", value=str(stats['winning_trades']), inline=True)
            embed.add_field(name="輸的交易", value=str(stats['losing_trades']), inline=True)
            embed.add_field(name="ROI", value=f"{format_number(stats['roi'])}%", inline=True)
            
            # 風險管理
            embed.add_field(
                name="風險配置",
                value=f"每筆風險: {Config.RISK_PER_TRADE_PERCENT}%\n"
                      f"最大倉位: {Config.MAX_POSITION_SIZE_PERCENT}%\n"
                      f"最大同時倉位: {Config.MAX_CONCURRENT_POSITIONS}",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='status', help='查看機器人狀態')
        async def status(ctx):
            embed = discord.Embed(
                title="🤖 機器人狀態",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="狀態", value="✅ 運行中", inline=True)
            embed.add_field(name="監控模式", value=Config.SYMBOL_MODE.upper(), inline=True)
            embed.add_field(name="監控幣種數", value=str(Config.MAX_SYMBOLS), inline=True)
            
            if self.risk_manager:
                open_pos = len(self.risk_manager.open_positions)
                embed.add_field(name="當前倉位", value=f"{open_pos}/3", inline=True)
            
            embed.add_field(name="交易模式", value="✅ 已啟用" if Config.ENABLE_TRADING else "⚠️ 模擬模式", inline=True)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='config', help='查看配置')
        async def config(ctx):
            embed = discord.Embed(
                title="⚙️ 機器人配置",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # 交易對配置
            embed.add_field(
                name="交易對配置",
                value=f"模式: {Config.SYMBOL_MODE}\n"
                      f"數量: {Config.MAX_SYMBOLS}",
                inline=False
            )
            
            # 風險管理配置
            embed.add_field(
                name="風險管理",
                value=f"每筆風險: {Config.RISK_PER_TRADE_PERCENT}%\n"
                      f"最大倉位: {Config.MAX_POSITION_SIZE_PERCENT}%\n"
                      f"同時倉位: {Config.MAX_CONCURRENT_POSITIONS}\n"
                      f"每倉位資金: {Config.CAPITAL_PER_POSITION_PERCENT:.2f}%",
                inline=False
            )
            
            # 止損止盈配置
            embed.add_field(
                name="止損止盈",
                value=f"止損 ATR 倍數: {Config.STOP_LOSS_ATR_MULTIPLIER}\n"
                      f"止盈 ATR 倍數: {Config.TAKE_PROFIT_ATR_MULTIPLIER}",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
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
    
    async def send_market_analysis(self, symbol, analysis):
        if not self.is_ready:
            return
        
        embed = discord.Embed(
            title=f"🔍 市場分析: {symbol}",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="當前價格", value=f"${format_number(analysis.get('price', 0))}", inline=True)
        embed.add_field(name="ATR", value=f"${format_number(analysis.get('atr', 0))}", inline=True)
        embed.add_field(name="市場結構", value=analysis.get('market_structure', 'N/A'), inline=True)
        
        if 'rsi' in analysis:
            embed.add_field(name="RSI", value=format_number(analysis['rsi']), inline=True)
        if 'macd_signal' in analysis:
            signal = "🟢 看漲" if analysis['macd_signal'] == 'bullish' else "🔴 看跌" if analysis['macd_signal'] == 'bearish' else "⚪ 中性"
            embed.add_field(name="MACD 信號", value=signal, inline=True)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending market analysis: {e}")
    
    async def send_signal(self, symbol, signal_info):
        if not self.is_ready:
            return
        
        signal_type = signal_info.get('type', 'UNKNOWN')
        color = discord.Color.green() if signal_type == 'BUY' else discord.Color.red() if signal_type == 'SELL' else discord.Color.blue()
        
        embed = discord.Embed(
            title=f"📡 交易信號: {symbol}",
            description=f"**{signal_type}** 信號檢測",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="入場價格", value=f"${format_number(signal_info.get('entry_price', 0))}", inline=True)
        embed.add_field(name="止損", value=f"${format_number(signal_info.get('stop_loss', 0))}", inline=True)
        embed.add_field(name="止盈", value=f"${format_number(signal_info.get('take_profit', 0))}", inline=True)
        
        if 'position_size' in signal_info:
            embed.add_field(name="建議倉位", value=format_number(signal_info['position_size'], 6), inline=True)
        
        if 'confidence' in signal_info:
            embed.add_field(name="信心度", value=f"{format_number(signal_info['confidence'])}%", inline=True)
        
        if 'expected_roi' in signal_info:
            embed.add_field(name="預期投報率", value=f"{format_number(signal_info['expected_roi'])}%", inline=True)
        
        if 'reason' in signal_info:
            embed.add_field(name="原因", value=signal_info['reason'], inline=False)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
    
    async def send_cycle_start(self, symbols_count, current_positions=0, max_positions=3):
        if not self.is_ready:
            return
        
        embed = discord.Embed(
            title="🔄 開始新的分析週期",
            description=f"監控 **{symbols_count}** 個交易對",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="當前倉位", value=f"{current_positions}/{max_positions}", inline=True)
        embed.add_field(name="可用倉位", value=str(max_positions - current_positions), inline=True)
        embed.add_field(name="倉位管理", value="資金3等分，最多持倉3個", inline=False)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending cycle start: {e}")
    
    async def send_cycle_complete(self, duration, signals_found, summary=None):
        if not self.is_ready:
            return
        
        embed = discord.Embed(
            title="✅ 分析週期完成",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="用時", value=f"{duration:.1f}秒", inline=True)
        embed.add_field(name="發現信號", value=str(signals_found), inline=True)
        
        if summary:
            embed.add_field(name="本週期總結", value=summary, inline=False)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending cycle complete: {e}")
    
    async def close(self):
        if self.bot:
            await self.bot.close()
            logger.info("Discord bot closed")
