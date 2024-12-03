import discord
import json
import os
from discord.ext import commands

# JSON kezelés
def readFromJSON():
    file_path = 'ticket/data.json'
    if not os.path.exists(file_path):
        default_data = {
            "ticket": {
                "channel": None,
                "role": None,
                "message": "",
                "category": None,
                "panel_message_id": None
            },
            "ticket_count": 0
        }
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def writeToJSON(data):
    file_path = 'ticket/data.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Hibajegy bezárása
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.danger, label="Hibajegy bezárása", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.channel.delete()


# Hibajegy nyitása
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, label="Hibajegy nyitása", custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Nem találtam szervert, kérlek próbáld újra.", ephemeral=True)
            return

        member = interaction.user
        data = readFromJSON()

        # Hibajegy számláló növelése
        ticket_count = data.get("ticket_count", 0) + 1
        data["ticket_count"] = ticket_count

        channel_name = f"ticket-{ticket_count:03d}"
        category_id = data["ticket"]["category"]
        category = discord.utils.get(guild.categories, id=category_id)

        if category is None:
            await interaction.response.send_message("Hibás kategória ID. Ellenőrizd a beállításokat.", ephemeral=True)
            return

        # Csatorna létrehozása
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            topic=f"Ticket for {member.name}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
        )

        staff_role_id = data["ticket"]["role"]
        staff_role = guild.get_role(staff_role_id)
        if staff_role:
            await ticket_channel.set_permissions(staff_role, read_messages=True, send_messages=True)

        # Bezárás gomb hozzáadása
        close_embed = discord.Embed(
            title="Hibajegy bezárása",
            description="Kattints a gombra a hibajegy bezárásához.",
            color=discord.Color.red()
        )
        await ticket_channel.send(embed=close_embed, view=CloseTicketView())

        await interaction.response.send_message(f"Hibajegy létrehozva: {ticket_channel.mention}", ephemeral=True)
        writeToJSON(data)


# Panel újraalkotása
async def recreate_ticket_panel(bot):
    data = readFromJSON()
    ticket_info = data.get("ticket", {})

    if not all(k in ticket_info for k in ["channel", "message", "panel_message_id"]):
        return

    channel_id = ticket_info["channel"]
    message_content = ticket_info["message"]
    panel_message_id = ticket_info["panel_message_id"]

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    embed = discord.Embed(title="Hibajegy", description=" ")
    embed.add_field(name=" ", value=message_content)
    embed.set_thumbnail(url=channel.guild.icon.url if channel.guild.icon else None)
    embed.set_footer(text=channel.guild.name)

    view = TicketView()

    try:
        panel_message = await channel.fetch_message(panel_message_id)
        await panel_message.edit(embed=embed, view=view)
    except discord.NotFound:
        new_panel_message = await channel.send(embed=embed, view=view)
        data["ticket"]["panel_message_id"] = new_panel_message.id
        writeToJSON(data)


# Ticket beállítása
async def setticket(ctx, szöveg: str, csatorna: discord.TextChannel, rangok: discord.Role, kategória: discord.CategoryChannel):
    data = readFromJSON()
    data["ticket"].update({
        "channel": csatorna.id,
        "role": rangok.id,
        "message": szöveg,
        "category": kategória.id,
        "panel_message_id": None
    })
    writeToJSON(data)

    embed = discord.Embed(title="Hibajegy", description=" ")
    embed.add_field(name=" ", value=szöveg)
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text=ctx.guild.name)

    view = TicketView()
    panel_message = await csatorna.send(embed=embed, view=view)

    data["ticket"]["panel_message_id"] = panel_message.id
    writeToJSON(data)
    await ctx.send("Ticket rendszer beállítva!")


# Modul exportálása
__all__ = ['TicketView', 'CloseTicketView', 'setticket', 'recreate_ticket_panel']
