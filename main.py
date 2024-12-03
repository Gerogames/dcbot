import discord
from discord.ext import commands
import json
from tokenek import TOKEN
from PIL import Image, ImageDraw, ImageFont
from ticket import TicketView, CloseTicketView, setticket, recreate_ticket_panel, recreate_close_buttons
#teszt
import io
import requests

# Bot inicializálása az összes intenttel
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# JSON olvasás/írás funkciók
def read_json():
    default_data = {
        'welcome': {
            'enabled': True,
            'channel_id': 1312445801288695928,
            'message': ''
        },
        'goodbye': {
            'enabled': True,
            'channel_id': 1312445801288695928,
            'message': ''
        }
    }
    try:
        with open('welcomeGoodbye/data.json', 'r') as f:
            data = json.load(f)
        # Hiányzó kulcsok pótlása
        for key in default_data:
            if key not in data:
                data[key] = default_data[key]
            else:
                for subkey in default_data[key]:
                    if subkey not in data[key]:
                        data[key][subkey] = default_data[key][subkey]
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data

def write_json(data):
    with open('welcomeGoodbye/data.json', 'w') as f:
        json.dump(data, f, indent=4)

# Üdvözlő kép készítése háttérrel
def create_welcome_image(user_name, profile_picture_url):
    try:
        # Háttérkép betöltése
        background = Image.open("background.png").convert("RGBA")
        image = background.copy()  # Másolat készítése módosításokhoz
        draw = ImageDraw.Draw(image)

        # Betűtípus betöltése
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 50)

        # Szöveg hozzáadása
        text = f"Üdvözlünk, {user_name}!"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]

        draw.text(((800 - text_width) // 2, 20), text, font=font, fill=(255, 255, 255))

        # Profilkép letöltése
        profile_picture = Image.open(io.BytesIO(requests.get(profile_picture_url).content))
        profile_picture = profile_picture.resize((120, 120)).convert("RGBA")

        # Profilkép szegéllyel
        border = Image.new("RGBA", (124, 124), (255, 255, 255, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse((2, 2, 122, 122), outline="white", width=5)

        mask = Image.new("L", profile_picture.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 120, 120), fill=255)
        profile_picture.putalpha(mask)

        bordered_picture = Image.new("RGBA", (124, 124), (255, 255, 255, 0))
        bordered_picture.paste(border, (0, 0))
        bordered_picture.paste(profile_picture, (2, 2), profile_picture)

        image.paste(bordered_picture, (340, 150), bordered_picture)

        # text.png hozzáadása
        text_image = Image.open("text.png").convert("RGBA")
        text_image = text_image.resize((280, 50))
        image.paste(text_image, (20, 350), text_image)

        # Discord logó hozzáadása
        logo = Image.open("logo.png").convert("RGBA").resize((80, 80))
        logo_mask = Image.new("L", logo.size, 0)
        logo_draw_mask = ImageDraw.Draw(logo_mask)
        logo_draw_mask.ellipse((0, 0, 80, 80), fill=255)
        logo.putalpha(logo_mask)
        image.paste(logo, (710, 300), logo)

        # Kép mentése memóriába
        output = io.BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error creating welcome image: {e}")
        return None

# Bot készen áll
@bot.event
async def on_ready():
    print("--------------------------------")
    print(f'{bot.user.name} online')
    print(f'ID: {bot.user.id}')
    print("--------------------------------")

    await recreate_ticket_panel()
    await recreate_close_buttons()

@bot.command(name="setticket", description="Ticket beállítása")
async def setticket_command(ctx, szöveg: str, csatorna: discord.TextChannel, rangok: discord.Role, kategória: discord.CategoryChannel):
    await setticket(ctx, szöveg, csatorna, rangok, kategória)

# Új tag érkezése
@bot.event
async def on_member_join(member):
    data = read_json()
    if data['welcome']['enabled']:
        channel = bot.get_channel(data['welcome']['channel_id'])
        if channel and data['welcome']['message']:
            try:
                message = data['welcome']['message'].format(
                    serverName=member.guild.name,
                    userName=member.name,
                    userMention=member.mention,
                    userCount=len(member.guild.members)
                )
                image_data = create_welcome_image(member.name, member.avatar.url)
                if image_data:
                    await channel.send(message, file=discord.File(image_data, "welcome_image.png"))
                else:
                    await channel.send(message)
            except Exception as e:
                print(f"Error sending welcome message: {e}")

# Tag kilépése
@bot.event
async def on_member_remove(member):
    data = read_json()
    if data['goodbye']['enabled']:
        channel = bot.get_channel(data['goodbye']['channel_id'])
        if channel and data['goodbye']['message']:
            try:
                message = data['goodbye']['message'].format(
                    serverName=member.guild.name,
                    userName=member.name,
                    userMention=member.mention,
                    userCount=len(member.guild.members)
                )
                await channel.send(message)
            except Exception as e:
                print(f"Error sending goodbye message: {e}")

# Bot futtatása
bot.run(TOKEN)
