import discord
from discord.ext import commands, tasks
import os
import sys

print("Bot başlatılıyor...")

# Bot ayarları
intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# SABIT AYARLAR - BUNLARI DÜZENLEYİN
KINDAR_ROLE_ID = 1458803684111552603  # @Kindar rolünün ID'sini buraya yazın
CHECK_INTERVAL = 30  # Kontrol aralığı (saniye)

# Bot hazır olduğunda
@bot.event
async def on_ready():
    print(f'Bot hazır: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Kindar rol ID: {KINDAR_ROLE_ID}')
    
    # Kontrolü başlat
    if not check_kindar_status.is_running():
        check_kindar_status.start()
    
    # Bot durumunu ayarla
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name='"kindar" durumunu'
        )
    )

# "kindar" durumu kontrolü
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_kindar_status():
    try:
        for guild in bot.guilds:
            # Kindar rolünü bul
            kindar_role = guild.get_role(KINDAR_ROLE_ID)
            if not kindar_role:
                print(f"Uyarı: {guild.name} sunucusunda Kindar rolü bulunamadı (ID: {KINDAR_ROLE_ID})")
                continue
            
            for member in guild.members:
                if member.bot or not member.activity:
                    continue
                
                # Durum metnini al ve küçük harfe çevir
                activity_text = str(member.activity.name).lower()
                
                # "kindar" kelimesini ara
                if "kindar" in activity_text:
                    # Eğer rolü yoksa ver
                    if kindar_role not in member.roles:
                        try:
                            await member.add_roles(kindar_role)
                            print(f"✅ {member.name} -> @{kindar_role.name} (Durum: {activity_text})")
                        except discord.Forbidden:
                            print(f"❌ {member.name} için rol verilemedi: Yetki yok")
                        except Exception as e:
                            print(f"❌ Hata: {e}")
                    # Eğer rolü varsa ve durumda "kindar" yoksa rolü al (isteğe bağlı)
                    # elif kindar_role in member.roles and "kindar" not in activity_text:
                    #     await member.remove_roles(kindar_role)
                    #     print(f"➖ {member.name} -> @{kindar_role.name} rolü alındı")
                
    except Exception as e:
        print(f"Kontrol hatası: {e}")

# Komut: Manuel kontrol
@bot.command(name='kontrol')
@commands.has_permissions(administrator=True)
async def kontrol_komut(ctx):
    """Tüm üyeleri 'kindar' durumu için kontrol eder"""
    mesaj = await ctx.send("🔍 Kindar durumu kontrol ediliyor...")
    
    kindar_role = ctx.guild.get_role(KINDAR_ROLE_ID)
    if not kindar_role:
        await mesaj.edit(content=f"❌ Kindar rolü bulunamadı! (ID: {KINDAR_ROLE_ID})")
        return
    
    eklenen = 0
    for member in ctx.guild.members:
        if member.bot or not member.activity:
            continue
        
        activity_text = str(member.activity.name).lower()
        
        if "kindar" in activity_text and kindar_role not in member.roles:
            try:
                await member.add_roles(kindar_role)
                eklenen += 1
            except:
                pass
    
    await mesaj.edit(content=f"✅ {eklenen} kişiye Kindar rolü verildi.")

# Komut: Kullanıcı kontrolü
@bot.command(name='kontrolet')
@commands.has_permissions(administrator=True)
async def kontrol_et(ctx, member: discord.Member = None):
    """Belirli bir kullanıcının durumunu kontrol eder"""
    if not member:
        member = ctx.author
    
    if member.bot:
        await ctx.send("🤖 Botları kontrol etmiyorum.")
        return
    
    kindar_role = ctx.guild.get_role(KINDAR_ROLE_ID)
    if not kindar_role:
        await ctx.send(f"❌ Kindar rolü bulunamadı! (ID: {KINDAR_ROLE_ID})")
        return
    
    if not member.activity:
        await ctx.send(f"📭 {member.mention} bir durum kullanmıyor.")
        return
    
    activity_text = str(member.activity.name)
    
    if "kindar" in activity_text.lower():
        if kindar_role not in member.roles:
            try:
                await member.add_roles(kindar_role)
                await ctx.send(f"✅ {member.mention} 'kindar' durumunda! Rol verildi.")
            except:
                await ctx.send(f"❌ {member.mention} 'kindar' durumunda ama rol verilemedi.")
        else:
            await ctx.send(f"ℹ️ {member.mention} zaten Kindar rolüne sahip.")
    else:
        await ctx.send(f"❌ {member.mention} 'kindar' durumunda değil.")

# Komut: Bilgi
@bot.command(name='bilgi')
async def bilgi_komut(ctx):
    """Bot hakkında bilgi verir"""
    kindar_role = ctx.guild.get_role(KINDAR_ROLE_ID)
    role_name = kindar_role.name if kindar_role else "Bulunamadı"
    
    embed = discord.Embed(
        title="🤖 Kindar Durum Botu",
        description="Bu bot, 'kindar' durumunu kullananlara otomatik rol verir.",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="👑 Kindar Rolü", value=f"{role_name} (ID: {KINDAR_ROLE_ID})", inline=False)
    embed.add_field(name="⏱️ Kontrol Aralığı", value=f"{CHECK_INTERVAL} saniye", inline=False)
    embed.add_field(name="📊 Toplam Sunucu", value=str(len(bot.guilds)), inline=False)
    
    # Aktif "kindar" kullanıcıları say
    if kindar_role:
        kindar_uyeler = len(kindar_role.members)
        embed.add_field(name="📈 Kindar Üyeler", value=str(kindar_uyeler), inline=False)
    
    await ctx.send(embed=embed)

# Komut: Yardım
@bot.command(name='yardim')
async def yardim_komut(ctx):
    embed = discord.Embed(
        title="❓ Yardım - Kindar Bot",
        description="**Kullanılabilir Komutlar:**",
        color=discord.Color.blue()
    )
    
    komutlar = [
        ("!kontrol", "Tüm sunucuyu 'kindar' durumu için tarar"),
        ("!kontrolet [@kullanıcı]", "Belirli kullanıcıyı kontrol eder"),
        ("!bilgi", "Bot hakkında bilgi verir"),
        ("!yardim", "Bu mesajı gösterir")
    ]
    
    for komut, aciklama in komutlar:
        embed.add_field(name=komut, value=aciklama, inline=False)
    
    embed.set_footer(text="Yalnızca 'kindar' durumunu kontrol eder")
    await ctx.send(embed=embed)

# Hata yönetimi
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komut için yönetici izni gerekiyor.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Eksik parametre! `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Geçersiz kullanıcı! @etiket şeklinde belirtin.")
    else:
        print(f"Hata: {error}")

# Botu başlat
if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")
    
    if TOKEN:
        print("Token bulundu, bot başlatılıyor...")
        bot.run(TOKEN)
    else:
        print("HATA: DISCORD_TOKEN bulunamadı!")
        print("Railway'de Environment Variables ekleyin:")
        print("Name: DISCORD_TOKEN")
        print("Value: bot_tokeniniz")
