import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

FAVELAS = [
    "São Remo",
    "Tiradentes",
    "Marcone",
    "Pantanal",
    "Paraisópolis",
    "Predinhos",
    "Vila dos Pescadores",
    "Vila Ede",
    "Pimentas",
    "Vitrinni",
    "Bololo"
]

# Ranking fica na memória do bot
ranking = {favela: 0 for favela in FAVELAS}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Bot online como {bot.user}")
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")


# =========================
# RANKING
# =========================

@bot.tree.command(
    name="ranking",
    description="Mostra o ranking de gastos das favelas"
)
async def ranking_comando(interaction: discord.Interaction):

    lista = sorted(
        ranking.items(),
        key=lambda item: item[1],
        reverse=True
    )

    texto = ""

    for posicao, (favela, valor) in enumerate(lista, start=1):

        if valor > 0 and posicao == 1:
            icone = "🥇"
        elif valor > 0 and posicao == 2:
            icone = "🥈"
        elif valor > 0 and posicao == 3:
            icone = "🥉"
        else:
            icone = f"**{posicao}º**"

        texto += f"{icone} **{favela}** — `${valor:,.0f}`\n"

    embed = discord.Embed(
        title="🏆 RANKING — CAMPO BELO",
        description=texto
    )

    await interaction.response.send_message(embed=embed)


# =========================
# ADICIONAR GASTO
# =========================

@bot.tree.command(
    name="adicionargasto",
    description="Adiciona dinheiro gasto por uma favela"
)
@app_commands.describe(
    favela="Nome da favela",
    valor="Valor gasto"
)
@app_commands.checks.has_permissions(administrator=True)
async def adicionar_gasto(
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    if favela not in FAVELAS:
        await interaction.response.send_message(
            "❌ Essa favela não está cadastrada.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )
        return

    ranking[favela] += valor

    await interaction.response.send_message(
        f"✅ **Gasto registrado!**\n\n"
        f"🏘️ Favela: **{favela}**\n"
        f"💰 Adicionado: **${valor:,.0f}**\n"
        f"📊 Total: **${ranking[favela]:,.0f}**"
    )


# =========================
# GASTO TOTAL
# =========================

@bot.tree.command(
    name="gastototal",
    description="Mostra quanto uma favela já gastou"
)
@app_commands.describe(
    favela="Nome da favela"
)
async def gasto_total(
    interaction: discord.Interaction,
    favela: str
):

    if favela not in FAVELAS:
        await interaction.response.send_message(
            "❌ Essa favela não está cadastrada.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"📊 **{favela}** já gastou "
        f"**${ranking[favela]:,.0f}**."
    )


# =========================
# REMOVER GASTO
# =========================

@bot.tree.command(
    name="removergasto",
    description="Remove dinheiro do total de uma favela"
)
@app_commands.describe(
    favela="Nome da favela",
    valor="Valor a remover"
)
@app_commands.checks.has_permissions(administrator=True)
async def remover_gasto(
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    if favela not in FAVELAS:
        await interaction.response.send_message(
            "❌ Essa favela não está cadastrada.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )
        return

    ranking[favela] = max(
        0,
        ranking[favela] - valor
    )

    await interaction.response.send_message(
        f"↩️ **Gasto corrigido!**\n\n"
        f"🏘️ Favela: **{favela}**\n"
        f"➖ Removido: **${valor:,.0f}**\n"
        f"📊 Total: **${ranking[favela]:,.0f}**"
    )


# =========================
# ZERAR RANKING
# =========================

@bot.tree.command(
    name="zerarranking",
    description="Zera todos os gastos"
)
@app_commands.checks.has_permissions(administrator=True)
async def zerar_ranking(
    interaction: discord.Interaction
):

    for favela in FAVELAS:
        ranking[favela] = 0

    await interaction.response.send_message(
        "⚠️ **Ranking zerado com sucesso!**"
    )


# =========================
# ERROS
# =========================

@bot.tree.error
async def erro_comando(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.MissingPermissions):

        mensagem = (
            "❌ Você precisa ter a permissão "
            "**Administrador** para usar esse comando."
        )

    else:

        print(f"Erro no comando: {error}")

        mensagem = (
            "❌ Ocorreu um erro ao executar o comando."
        )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                mensagem,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                mensagem,
                ephemeral=True
            )

    except Exception as erro:

        print(f"Erro ao enviar mensagem de erro: {erro}")


# =========================
# INICIAR BOT
# =========================

if not TOKEN:
    print("❌ DISCORD_TOKEN não foi encontrado!")

else:
    bot.run(TOKEN)
