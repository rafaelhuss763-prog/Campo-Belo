import os
import json
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
ARQUIVO = "ranking.json"

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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def carregar_ranking():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        for favela in FAVELAS:
            dados.setdefault(favela, 0)

        return dados

    except:
        return {favela: 0 for favela in FAVELAS}


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
    description="Mostra o ranking de gastos das favelas"
)
async def ranking_comando(interaction: discord.Interaction):

    lista = sorted(
        ranking.items(),
        key=lambda item: item[1],
        reverse=True
    )

    medalhas = ["🥇", "🥈", "🥉"]
    texto = ""

    for posicao, (favela, valor) in enumerate(lista, start=1):

        if posicao <= 3:
            colocacao = medalhas[posicao - 1]
        else:
            colocacao = f"**{posicao}º**"

        texto += f"{colocacao} **{favela}** — `${valor:,.0f}`\n"

    embed = discord.Embed(
        title="🏆 RANKING — CAMPO BELO",
        description=texto
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="adicionargasto",
    description="Adiciona um valor gasto por uma favela"
)
@app_commands.describe(
    favela="Nome da favela",
    valor="Valor gasto"
)
@app_commands.checks.has_permissions(administrator=True)
async def adicionar_gasto(
    interaction: discord.Interaction,
    favela: str,
    valor: float
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
    salvar_ranking()

    await interaction.response.send_message(
        f"✅ Gasto registrado!\n"
        f"🏘️ **{favela}**\n"
        f"💰 Gasto adicionado: **${valor:,.0f}**\n"
        f"📊 Total: **${ranking[favela]:,.0f}**"
    )


@bot.tree.command(
    name="gastototal",
    description="Consulta o total gasto por uma favela"
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


@bot.tree.command(
    name="removergasto",
    description="Remove um valor do total gasto"
)
@app_commands.describe(
    favela="Nome da favela",
    valor="Valor a remover"
)
@app_commands.checks.has_permissions(administrator=True)
async def remover_gasto(
    interaction: discord.Interaction,
    favela: str,
    valor: float
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

    salvar_ranking()

    await interaction.response.send_message(
        f"↩️ Gasto corrigido!\n"
        f"🏘️ **{favela}**\n"
        f"💰 Total agora: **${ranking[favela]:,.0f}**"
    )


@bot.tree.command(
    name="zerarranking",
    description="Zera todos os gastos do ranking"
)
@app_commands.checks.has_permissions(administrator=True)
async def zerar_ranking(
    interaction: discord.Interaction
):

    ranking.clear()

    for favela in FAVELAS:
        ranking[favela] = 0

    salvar_ranking()

    await interaction.response.send_message(
        "⚠️ **Ranking de gastos zerado com sucesso!**"
    )


bot.run(TOKEN)
