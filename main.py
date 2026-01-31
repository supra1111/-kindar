import discord
from discord.ext import commands, tasks
import os

# BOT AYARLARI - BURAYI DÜZENLEYİN
KINDAR_ROLE_ID = 123456789012345678  # @Kindar rol ID'sini yazın

# Bot kurulumu
intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Bot hazır olduğunda
@bot.event
async def on_ready():
    print(f'✅ BOT HAZIR: {bot.user.name}')
    print(f'👑 KINDAR ROL ID: {KINDAR_ROLE_ID}')
    
    # Otomatik kontrolü başlat
    if not check_kindar.is_running():
        check_kindar.start()

# Her 30 saniyede bir kontrol
@tasks.loop(seconds=30)
async def check_kindar():
    for sunucu in bot.guilds:
        # Kindar rolünü bul
        kindar_rol = sunucu.get_role(KINDAR_ROLE_ID)
        if not kindar_rol:
            print(f"⚠️ {sunucu.name}: Kindar rolü yok!")
            continue
        
        # Tüm üyeleri kontrol et
        for uye in sunucu.members:
            if uye.bot:  # Botları atla
                continue
            
            if not uye.activity:  # Durumu yoksa atla
                continue
            
            # Durum metnini al
            durum = str(uye.activity.name).lower()
            
            # "kindar" kelimesini ara
            if "kindar" in durum:
                # Rolü yoksa ver
                if kindar_rol not in uye.roles:
                    try:
                        await uye.add_roles(kindar_rol)
                        print(f"✅ {uye.name} -> @{kindar_rol.name}")
                    except:
                        print(f"❌ {uye.name} için rol verilemedi")

# Komut: !kontrol
@bot.command()
async def kontrol(ctx):
    """Kindar durumunu kontrol eder"""
    kindar_rol = ctx.guild.get_role(KINDAR_ROLE_ID)
    
    if not kindar_rol:
        await ctx.send("❌ Kindar rolü bulunamadı!")
        return
    
    sayac = 0
    for uye in ctx.guild.members:
        if uye.bot or not uye.activity:
            continue
        
        durum = str(uye.activity.name).lower()
        
        if "kindar" in durum and kindar_rol not in uye.roles:
            try:
                await uye.add_roles(kindar_rol)
                sayac += 1
            except:
                pass
    
    await ctx.send(f"✅ {sayac} kişiye Kindar rolü verildi!")

# Komut: !bilgi
@bot.command()
async def bilgi(ctx):
    """Bot bilgilerini gösterir"""
    kindar_rol = ctx.guild.get_role(KINDAR_ROLE_ID)
    rol_adi = kindar_rol.name if kindar_rol else "BULUNAMADI"
    
    await ctx.send(f"""
🤖 **KINDAR BOT**
👑 **Rol:** {rol_adi}
🆔 **Rol ID:** {KINDAR_ROLE_ID}
⚡ **Komut:** !kontrol
📝 **Açıklama:** "kindar" yazanlara otomatik rol verir
    """)

# BOTU BAŞLAT
TOKEN = os.environ.get("DISCORD_TOKEN")

if TOKEN:
    print("🚀 Bot başlatılıyor...")
    bot.run(TOKEN)
else:
    print("""
❌ **HATA: TOKEN BULUNAMADI!**
    
Railway'de şu adımları takip edin:
1. Proje ayarlarına gir
2. "Variables" sekmesine tıkla
3. "New Variable" butonuna tıkla
4. Name: DISCORD_TOKEN
5. Value: bot_tokeniniz
6. Deploy et
    """)
