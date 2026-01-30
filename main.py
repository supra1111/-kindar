import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

# .env dosyasından token'ı yükle
load_dotenv()

# Bot intents (izinlerini) ayarla
intents = discord.Intents.default()
intents.members = True
intents.presences = True

# Bot prefix'i ve intents ile başlat
bot = commands.Bot(command_prefix='!', intents=intents)

# Yapılandırma için sözlük
status_roles = {}

# Bot hazır olduğunda
@bot.event
async def on_ready():
    print(f'{bot.user.name} botu olarak giriş yapildi.')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    
    # Yapılandırmayı yükle
    load_config()
    
    # Durum kontrolünü başlat
    check_statuses.start()

# Yapılandırmayı dosyadan yükle
def load_config():
    try:
        with open('status_roles.txt', 'r') as file:
            for line in file:
                if ':' in line:
                    status, role_id = line.strip().split(':')
                    status_roles[status] = int(role_id)
        print(f"{len(status_roles)} adet durum-rol eslesmesi yuklendi.")
    except FileNotFoundError:
        print("status_roles.txt dosyasi bulunamadi. Yeni dosya olusturulacak.")
        save_config()
    except Exception as e:
        print(f"Yapılandırma yüklenirken hata: {e}")

# Yapılandırmayı dosyaya kaydet
def save_config():
    try:
        with open('status_roles.txt', 'w') as file:
            for status, role_id in status_roles.items():
                file.write(f"{status}:{role_id}\n")
        print("Yapilandirma kaydedildi.")
    except Exception as e:
        print(f"Yapilandirma kaydedilirken hata: {e}")

# Durum kontrolü - her 30 saniyede bir çalışır
@tasks.loop(seconds=30)
async def check_statuses():
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot and member.activity:
                activity_name = str(member.activity.name).lower()
                await assign_role_based_on_status(member, activity_name, guild)

# Duruma göre rol atama
async def assign_role_based_on_status(member, activity_name, guild):
    for status_text, role_id in status_roles.items():
        if status_text.lower() in activity_name:
            try:
                role = guild.get_role(role_id)
                if role and role not in member.roles:
                    await member.add_roles(role)
                    print(f"{member.name} kullanicisina '{role.name}' rolu verildi (Durum: {activity_name})")
            except discord.Forbidden:
                print(f"Rol vermek icin yeterli izin yok: {role_id}")
            except discord.HTTPException as e:
                print(f"Rol verilirken hata: {e}")

# Komut: Durum-rol eslesmesi ekle
@bot.command(name='durumrol_ekle')
@commands.has_permissions(administrator=True)
async def add_status_role(ctx, durum_metni: str, rol: discord.Role):
    status_roles[durum_metni.lower()] = rol.id
    save_config()
    
    embed = discord.Embed(
        title="Durum-Rol Eslesmesi Eklendi",
        description=f"'{durum_metni}' durumunu kullananlara {rol.name} rolu otomatik verilecek.",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# Komut: Durum-rol eslesmesi sil
@bot.command(name='durumrol_sil')
@commands.has_permissions(administrator=True)
async def remove_status_role(ctx, durum_metni: str):
    durum_metni = durum_metni.lower()
    
    if durum_metni in status_roles:
        removed_role_id = status_roles.pop(durum_metni)
        save_config()
        
        role = ctx.guild.get_role(removed_role_id)
        role_name = role.name if role else "Bilinmeyen Rol"
        
        embed = discord.Embed(
            title="Durum-Rol Eslesmesi Silindi",
            description=f"'{durum_metni}' durumu icin {role_name} rol atamasi kaldirildi.",
            color=0xff9900
        )
    else:
        embed = discord.Embed(
            title="Hata",
            description=f"'{durum_metni}' durumu icin kayitli bir rol bulunamadi.",
            color=0xff0000
        )
    
    await ctx.send(embed=embed)

# Komut: Aktif durum-rol eslesmelerini listele
@bot.command(name='durumrol_liste')
@commands.has_permissions(administrator=True)
async def list_status_roles(ctx):
    if not status_roles:
        embed = discord.Embed(
            title="Durum-Rol Eslesmeleri",
            description="Henuz hic durum-rol eslesmesi eklenmemis.",
            color=0x0000ff
        )
    else:
        embed = discord.Embed(
            title="Durum-Rol Eslesmeleri",
            description="Aktif durum-rol eslesmeleri:",
            color=0x0000ff
        )
        
        for status_text, role_id in status_roles.items():
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else "Rol Bulunamadi"
            embed.add_field(name=f"Durum: {status_text}", value=f"Rol: {role_name}", inline=False)
    
    await ctx.send(embed=embed)

# Komut: Manuel durum kontrolü yap
@bot.command(name='durum_kontrol')
@commands.has_permissions(administrator=True)
async def manual_status_check(ctx):
    message = await ctx.send("Durumlar kontrol ediliyor...")
    
    counter = 0
    for member in ctx.guild.members:
        if not member.bot and member.activity:
            activity_name = str(member.activity.name).lower()
            await assign_role_based_on_status(member, activity_name, ctx.guild)
            counter += 1
    
    await message.edit(content=f"Durum kontrolu tamamlandi. {counter} uye kontrol edildi.")

# Komut: Kullanıcı durumuna göre rol ver
@bot.command(name='rol_ver')
@commands.has_permissions(administrator=True)
async def give_role_by_status(ctx, member: discord.Member):
    if not member.activity:
        await ctx.send(f"{member.mention} kullanicisinin aktif bir durumu yok.")
        return
    
    activity_name = str(member.activity.name).lower()
    await assign_role_based_on_status(member, activity_name, ctx.guild)
    await ctx.send(f"{member.mention} kullanicisinin durumu kontrol edildi ve rol atamasi yapildi.")

# Komut: Bot hakkında bilgi
@bot.command(name='yardim')
async def help_command(ctx):
    embed = discord.Embed(
        title="Durum Rol Botu Komutlari",
        description="Asagida kullanabileceginiz komutlar listelenmistir.",
        color=0x0000ff
    )
    
    commands_list = [
        ("!durumrol_ekle <durum> <rol>", "Belirtilen durumu kullananlara rol verir"),
        ("!durumrol_sil <durum>", "Durum-rol eslesmesini siler"),
        ("!durumrol_liste", "Aktif durum-rol eslesmelerini listeler"),
        ("!durum_kontrol", "Tum uyelerin durumlarini kontrol eder"),
        ("!rol_ver <kullanici>", "Kullanicinin durumuna gore rol verir"),
        ("!yardim", "Bu yardim mesajini gosterir")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Not: Tum komutlar yonetici izni gerektirir.")
    await ctx.send(embed=embed)

# Hata yonetimi
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Bu komutu kullanmak icin Yonetici iznine sahip olmalisiniz.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Eksik parametre. Dogru kullanim: {ctx.prefix}{ctx.command.name} {ctx.command.signature}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Gecersiz parametre. Lutfen dogru formatta girin.")
    else:
        await ctx.send(f"Bir hata olustu: {str(error)}")

# Bot token'ını al ve çalıştır
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("HATA: DISCORD_TOKEN .env dosyasinda bulunamadi.")
    print("Lutfen .env dosyasi olusturun ve icine DISCORD_TOKEN='bot_tokeniniz' yazin.")
