import os
import json
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
ARQUIVO = "ranking.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def carregar_ranking():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except:
        return {}

def salvar_ranking():
    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(ranking, arquivo, ensure_ascii=False, indent=2)

ranking = carregar_ranking()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online como {bot.user}")


@bot.tree.command(
    name="ranking",
    description="Mostra o ranking das favelas"
)
async def ranking_comando(interaction: discord.Interaction):

    if not ranking:
        await interaction.response.send_message(
            "🏆 Ainda não existem registros no ranking."
        )
        return

    lista = sorted(
        ranking.items(),
        key=lambda item: item[1],
        reverse=True
    )

    medalhas = ["🥇", "🥈", "🥉"]
    texto = ""

    for posicao, (favela, pontos) in enumerate(lista, start=1):

        if posicao <= 3:
            colocacao = medalhas[posicao - 1]
        else:
            colocacao = f"**{posicao}º**"

        texto += f"{colocacao} **{favela}** — `{pontos}`\n"

    embed = discord.Embed(
        title="🏆 RANKING — CAMPO BELO",
        description=texto
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="pontos",
    description="Consulta os pontos de uma favela"
)
@app_commands.describe(
    favela="Nome da favela"
)
async def consultar_pontos(
    interaction: discord.Interaction,
    favela: str
):

    pontos = ranking.get(favela, 0)

    await interaction.response.send_message(
        f"📊 **{favela}** possui **{pontos} ponto(s)**."
    )


@bot.tree.command(
    name="adicionarponto",
    description="Adiciona 1 ponto para uma favela"
)
@app_commands.describe(
    favela="Nome da favela"
)
@app_commands.checks.has_permissions(administrator=True)
async def adicionar_ponto(
    interaction: discord.Interaction,
    favela: str
):

    ranking[favela] = ranking.get(favela, 0) + 1
    salvar_ranking()

    await interaction.response.send_message(
        f"✅ Registro realizado!\n"
        f"🏆 **{favela}** recebeu **+1 ponto**.\n"
        f"📊 Total: **{ranking[favela]}**"
    )


@bot.tree.command(
    name="removerponto",
    description="Remove 1 ponto de uma favela"
)
@app_commands.describe(
    favela="Nome da favela"
)
@app_commands.checks.has_permissions(administrator=True)
async def remover_ponto(
    interaction: discord.Interaction,
    favela: str
):

    ranking[favela] = max(
        0,
        ranking.get(favela, 0) - 1
    )

    salvar_ranking()

    await interaction.response.send_message(
        f"↩️ **{favela}** ficou com "
        f"**{ranking[favela]} ponto(s)**."
    )


@bot.tree.command(
    name="zerarranking",
    description="Zera todo o ranking"
)
@app_commands.checks.has_permissions(administrator=True)
async def zerar_ranking(
    interaction: discord.Interaction
):

    ranking.clear()
    salvar_ranking()

    await interaction.response.send_message(
        "⚠️ **Ranking zerado com sucesso!**"
    )


bot.run(TOKEN)
