import discord, os, asyncio
from discord.ext import commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# AYARLAR
TICKET_KATEGORI_ID = 1519782776067330078
DESTEK_EKIBI_ROL_ID = 1514015410318479440
EKSTRA_YETKILI_ROL_ID = 1484932780902191104
ETKINLIK_ROL_ID = 1520077448358658138
ONAY_RED_KANAL_ID = 1484933527668785323 
LOGO_URL = "https://cdn.discordapp.com/attachments/1454857856326176850/1520391008490356756/image.png"
TICKET_BANNER = "https://media.discordapp.com/attachments/1484952515635318846/1484955416327749783/14.png"

# --- TICKET YÖNETİM ---
class TicketYonetimView(View):
    def __init__(self): super().__init__(timeout=None)

    def is_authorized(self, user: discord.Member):
        return any(role.id in [1514015410318479440, 1484932780902191104] for role in user.roles)

    @discord.ui.button(label="Onay ✅", style=discord.ButtonStyle.green, custom_id="TICKET_ONAY_BTN")
    async def onay(self, i: discord.Interaction, b: Button):
        if not self.is_authorized(i.user): return await i.response.send_message("Yetkin yok!", ephemeral=True)
        
        # Kanal ismini değiştir
        await i.channel.edit(name=f"alındı-{i.channel.name.split('-')[-1]}")
        
        log_kanal = i.guild.get_channel(ONAY_RED_KANAL_ID)
        if log_kanal:
            user_id = i.channel.topic
            await log_kanal.send(f"<@{user_id}> başvurunuz onaylandı ✅")
        await i.response.send_message(f"Başvuru {i.user.mention} tarafından onaylandı!", ephemeral=False)

    @discord.ui.button(label="Red ❌", style=discord.ButtonStyle.red, custom_id="TICKET_RED_BTN")
    async def red(self, i: discord.Interaction, b: Button):
        if not self.is_authorized(i.user): return await i.response.send_message("Yetkin yok!", ephemeral=True)
        log_kanal = i.guild.get_channel(ONAY_RED_KANAL_ID)
        if log_kanal:
            user_id = i.channel.topic
            await log_kanal.send(f"<@{user_id}> başvurunuz reddedildi ❌")
        await i.response.send_message("Başvuru reddedildi. Kanal 5 saniye içinde silinecektir.", ephemeral=False)
        await asyncio.sleep(5)
        await i.channel.delete()

    @discord.ui.button(label="Kapat 🔒", style=discord.ButtonStyle.secondary, custom_id="TICKET_KAPAT_BTN")
    async def kapat(self, i: discord.Interaction, b: Button):
        if not self.is_authorized(i.user): return await i.response.send_message("Yetkin yok!", ephemeral=True)
        
        user_id = int(i.channel.topic)
        user = i.guild.get_member(user_id)
        
        # Kullanıcının kanalı görme iznini kapat
        if user:
            await i.channel.set_permissions(user, read_messages=False, send_messages=False)
        await i.response.send_message(f"Kanal kapatıldı ve başvuru sahibi erişimi kesildi.", ephemeral=False)

# --- TICKET PANEL ---
class TicketPaneliView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Başvuru Yap 📝", style=discord.ButtonStyle.blurple, custom_id="TICKET_BTN_UNIQUE_999")
    async def basvuru(self, i: discord.Interaction, b: Button):
        await i.response.defer(ephemeral=True)
        
        # İzinleri tanımla
        overwrites = {
            i.guild.default_role: discord.PermissionOverwrite(read_messages=False), 
            i.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Rolleri çek
        rol1 = i.guild.get_role(1514015410318479440)
        rol2 = i.guild.get_role(1484932780902191104)
        
        # Her iki role de kanalı görme izni ver
        if rol1: overwrites[rol1] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        if rol2: overwrites[rol2] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        
        kanal = await i.guild.create_text_channel(name=f"başvuru-{i.user.name}", category=i.guild.get_channel(TICKET_KATEGORI_ID), overwrites=overwrites, topic=str(i.user.id))
        
        # Etiketleme: Sadece rol1 etiketlenir
        etiket = f"{rol1.mention if rol1 else ''}"
        await kanal.send(f"{i.user.mention} {etiket}\n**📝 BAŞVURU FORMU**\n\n**Yaş? :**\n**MDRP'de kaç fps alıyorsun? :**\n**Önceden bulunduğun oluşumlar? :**\n**FiveM'de kaç saatiniz var? :**\n**Map bilginiz ?/10 :**\n**Referans? :**\n**En az 5 kill pov (Md Pov Zorunlu) :**")
        await kanal.send("**Yönetim İşlemleri:**", view=TicketYonetimView())
        await i.followup.send(f"Başvuru odan oluşturuldu: {kanal.mention}", ephemeral=True)

# --- INGAME ---
class EtkinlikView(View):
    def __init__(self, ad, limit):
        super().__init__(timeout=None)
        self.ad, self.limit, self.liste = ad, limit, []
    
    def get_embed(self):
        e = discord.Embed(title="Ravens Ingame", description=f"**Etkinlik:** {self.ad}\n**Kapasite:** {len(self.liste)}/{self.limit}", color=discord.Color.blue())
        e.set_thumbnail(url=LOGO_URL)
        e.add_field(name=f"👥 Katılanlar ({len(self.liste)})", value="\n".join([f"**{i+1}.** <@{u}>" for i, u in enumerate(self.liste)]) or "Henüz kimse katılmadı.", inline=False)
        return e

    @discord.ui.button(label="Etkinliğe Katıl ✅", style=discord.ButtonStyle.green, custom_id="INGAME_KATIL_888")
    async def katil(self, i: discord.Interaction, b: Button):
        if i.user.id not in self.liste:
            if len(self.liste) >= self.limit: return await i.response.send_message("Etkinlik kapasitesi dolu!", ephemeral=True)
            self.liste.append(i.user.id)
            if (role := i.guild.get_role(ETKINLIK_ROL_ID)): await i.user.add_roles(role)
            if len(self.liste) >= self.limit: self.children[0].disabled = True
            await i.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Etkinlikten Ayrıl ❌", style=discord.ButtonStyle.red, custom_id="INGAME_AYRIL_777")
    async def ayril(self, i: discord.Interaction, b: Button):
        if i.user.id in self.liste:
            self.liste.remove(i.user.id)
            if (role := i.guild.get_role(ETKINLIK_ROL_ID)): await i.user.remove_roles(role)
            self.children[0].disabled = False
            await i.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Etkinliği Bitir 🏁", style=discord.ButtonStyle.secondary, custom_id="INGAME_BITIR_666")
    async def bitir(self, i: discord.Interaction, b: Button):
        if i.user.guild_permissions.manage_messages:
            await i.response.defer()
            rol = i.guild.get_role(ETKINLIK_ROL_ID)
            if rol:
                for user_id in self.liste:
                    member = i.guild.get_member(user_id) or await i.guild.fetch_member(user_id)
                    if member:
                        try: await member.remove_roles(rol)
                        except: pass
            txt = "\n".join([f"**{i+1}.** <@{u}>" for i, u in enumerate(self.liste)])
            embed = discord.Embed(title=f"🏁 {self.ad} Etkinliği Bitti!", description=f"**Katılımcı Listesi:**\n{txt if self.liste else 'Katılımcı yok.'}", color=discord.Color.gold())
            await i.channel.send(embed=embed)
            await i.message.delete()
        else: await i.response.send_message("Yetkin yok!", ephemeral=True)

@bot.command()
async def ticket_paneli(ctx):
    await ctx.message.delete()
    e = discord.Embed(title="🎫 Ticket Sistemi - Destek", description="Başvuru Açıp Şansını Deneyebilirsin!", color=discord.Color.red())
    e.set_thumbnail(url=LOGO_URL)
    e.set_image(url=TICKET_BANNER)
    await ctx.send(embed=e, view=TicketPaneliView())

@bot.command()
async def ingame(ctx, *, args: str):
    await ctx.message.delete()
    parts = args.split()
    try:
        limit = int(parts[-1])
        ad = " ".join(parts[:-1])
    except: return await ctx.send("Hatalı kullanım! Doğrusu: !ingame [Etkinlik Adı] [Sayı]\nÖrnek: !ingame 22.00 Redzone Tik 20")
    v = EtkinlikView(ad, limit)
    await ctx.send(embed=v.get_embed(), view=v)

@bot.event
async def on_ready():
    bot.add_view(TicketPaneliView())
    bot.add_view(TicketYonetimView())
    print(f"✅ {bot.user} aktif ve butonlar sisteme tanıtıldı.")

bot.run(os.environ['TOKEN'])
