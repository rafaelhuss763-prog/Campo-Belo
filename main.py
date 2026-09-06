import os
import re
import discord
from discord import app_commands

# =========================================================
# CONFIGURAÇÃO
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# COLOQUE AQUI OS SEUS 3 NOVOS WEBHOOKS
WEBHOOK_ADICIONAR = "https://discord.com/api/webhooks/1546272715818672218/M2uvS74jTofIkxj_mkR70p-YaiTgYpmUHnYNnDe70NcrJCRoOlGDdinlQRDf7z_5Vt6T"
WEBHOOK_REMOVER = "https://discord.com/api/webhooks/1546273099987554389/j3yWVi6gLdx8saZKuoQ4L2MHe8BcoBaIHgzeQWSRALVfpBrcuYdX9YXR6uXWFi7ptoDd"
WEBHOOK_RANKING = "https://discord.com/api/webhooks/1546273377541423124/8M1YJqPtCkcZ-Z9RGfCMrRk0_7xFpufUBUoW5PH-KLGfDbLPstm-c7s8co3LKIUwD1gF"

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

MARCADOR = "CAMPO_BELO_RANKING_V3"

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

ranking_message = None


# =========================================================
# FORMATAÇÃO
# =========================================================

def novo_ranking():
    return {favela: 0 for favela in FAVELAS}


def dinheiro(valor):
    return f"R$ {valor:,}".replace(",", ".")


def criar_embed(dados):

    ranking = sorted(
        dados.items(),
        key=lambda item: item[1],
        reverse=True
    )

    linhas = []

    for posicao, (favela, valor) in enumerate(ranking, 1):

        if posicao == 1:
            emoji = "🥇"
        elif posicao == 2:
            emoji = "🥈"
        elif posicao == 3:
            emoji = "🥉"
        else:
            emoji = f"{posicao}º"

        linhas.append(
            f"{emoji} **{favela}** — **{dinheiro(valor)}**"
        )

    embed = discord.Embed(
        title="🏆 RANKING CAMPO BELO",
        description="\n".join(linhas),
        color=discord.Color.gold()
    )

    # Os valores ficam escondidos no footer para o bot conseguir
    # recuperar os dados depois de reiniciar.
    dados_salvos = "|".join(
        f"{favela}={dados[favela]}"
        for favela in FAVELAS
    )

    embed.set_footer(
        text=f"{MARCADOR}|{dados_salvos}"
    )

    return embed


def ler_ranking(message):

    dados = novo_ranking()

    if not message.embeds:
        return dados

    embed = message.embeds[0]

    if not embed.footer:
        return dados

    texto = embed.footer.text or ""

    if not texto.startswith(MARCADOR):
        return dados

    try:

        parte_dados = texto.split("|", 1)[1]

        partes = parte_dados.split("|")

        for parte in partes:

            if "=" not in parte:
                continue

            favela, valor = parte.rsplit("=", 1)

            if favela in dados:

                dados[favela] = int(valor)

    except Exception as erro:

        print(
            f"Erro lendo ranking: {erro}"
        )

    return dados


# =========================================================
# PROCURAR RANKING
# =========================================================

async def procurar_ranking():

    global ranking_message

    # Tenta usar a mensagem já encontrada
    if ranking_message is not None:

        try:

            mensagem = await ranking_message.channel.fetch_message(
                ranking_message.id
            )

            if mensagem.embeds:

                footer = mensagem.embeds[0].footer

                if footer and footer.text.startswith(MARCADOR):

                    ranking_message = mensagem

                    return mensagem

        except Exception:

            ranking_message = None

    # Procura o ranking nos canais
    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                async for message in channel.history(limit=100):

                    if message.author.id != bot.user.id:
                        continue

                    if not message.embeds:
                        continue

                    footer = message.embeds[0].footer

                    if not footer:
                        continue

                    if footer.text.startswith(MARCADOR):

                        ranking_message = message

                        print(
                            f"Ranking encontrado no canal #{channel.name}"
                        )

                        return message

            except Exception as erro:

                print(
                    f"Erro no canal #{channel.name}: {erro}"
                )

    return None


# =========================================================
# CARREGAR
# =========================================================

async def carregar_ranking():

    message = await procurar_ranking()

    if message is None:
        return None

    return ler_ranking(message)


# =========================================================
# ATUALIZAR
# =========================================================

async def atualizar_ranking(dados):

    global ranking_message

    if ranking_message is None:
        ranking_message = await procurar_ranking()

    if ranking_message is None:
        return False

    try:

        await ranking_message.edit(
            embed=criar_embed(dados)
        )

        return True

    except Exception as erro:

        print(
            f"Erro atualizando ranking: {erro}"
        )

        ranking_message = None

        return False


# =========================================================
# WEBHOOK
# =========================================================

async def enviar_webhook(url, embed):

    if not url:
        return

    if url.startswith("COLE_AQUI"):
        return

    try:

        webhook = discord.Webhook.from_url(
            url,
            client=bot
        )

        await webhook.send(
            embed=embed,
            username="Campo Belo Logs",
            wait=False
        )

    except Exception as erro:

        print(
            f"Erro no webhook: {erro}"
        )


# =========================================================
# LOG ADICIONAR
# =========================================================

async def log_adicionar(
    usuario,
    favela,
    valor,
    total
):

    embed = discord.Embed(
        title="➕ GASTO ADICIONADO",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Responsável",
        value=usuario.mention,
        inline=False
    )

    embed.add_field(
        name="🏘️ Favela",
        value=favela,
        inline=True
    )

    embed.add_field(
        name="💰 Valor adicionado",
        value=dinheiro(valor),
        inline=True
    )

    embed.add_field(
        name="📊 Novo total",
        value=dinheiro(total),
        inline=False
    )

    await enviar_webhook(
        WEBHOOK_ADICIONAR,
        embed
    )


# =========================================================
# LOG REMOVER
# =========================================================

async def log_remover(
    usuario,
    favela,
    valor,
    total
):

    embed = discord.Embed(
        title="➖ GASTO REMOVIDO",
        color=discord.Color.red()
    )

    embed.add_field(
        name="👤 Responsável",
        value=usuario.mention,
        inline=False
    )

    embed.add_field(
        name="🏘️ Favela",
        value=favela,
        inline=True
    )

    embed.add_field(
        name="💰 Valor removido",
        value=dinheiro(valor),
        inline=True
    )

    embed.add_field(
        name="📊 Novo total",
        value=dinheiro(total),
        inline=False
    )

    await enviar_webhook(
        WEBHOOK_REMOVER,
        embed
    )


# =========================================================
# LOG RANKING
# =========================================================

async def log_geral(
    titulo,
    descricao
):

    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=discord.Color.blue()
    )

    await enviar_webhook(
        WEBHOOK_RANKING,
        embed
    )


# =========================================================
# CRIAR RANKING
# =========================================================

@tree.command(
    name="criarranking",
    description="Cria o ranking das favelas"
)
async def criarranking(
    interaction: discord.Interaction
):

    global ranking_message

    await interaction.response.defer(
        ephemeral=True
    )

    existente = await procurar_ranking()

    if existente:

        await interaction.followup.send(
            "⚠️ Já existe um ranking neste servidor.",
            ephemeral=True
        )

        return

    dados = novo_ranking()

    ranking_message = await interaction.channel.send(
        embed=criar_embed(dados)
    )

    await log_geral(
        "🏆 RANKING CRIADO",
        f"👤 Criado por: {interaction.user.mention}\n"
        f"📍 Canal: {interaction.channel.mention}"
    )

    await interaction.followup.send(
        "✅ Ranking criado com sucesso!",
        ephemeral=True
    )


# =========================================================
# RANKING
# =========================================================

@tree.command(
    name="ranking",
    description="Mostra o ranking atual"
)
async def ranking(
    interaction: discord.Interaction
):

    await interaction.response.defer(
        ephemeral=True
    )

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ O ranking ainda não foi criado.",
            ephemeral=True
        )

        return

    embed = criar_embed(dados)

    await interaction.followup.send(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# ADICIONAR GASTO
# =========================================================

@tree.command(
    name="adicionargasto",
    description="Adiciona um gasto para uma favela"
)
@app_commands.describe(
    favela="Favela que realizou a compra",
    valor="Valor gasto"
)
async def adicionargasto(
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    await interaction.response.defer(
        ephemeral=True
    )

    if favela not in FAVELAS:

        await interaction.followup.send(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.followup.send(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ O ranking ainda não foi criado. Use `/criarranking`.",
            ephemeral=True
        )

        return

    dados[favela] += valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar o ranking.",
            ephemeral=True
        )

        return

    await log_adicionar(
        interaction.user,
        favela,
        valor,
        dados[favela]
    )

    await interaction.followup.send(
        f"✅ **{favela}** recebeu **{dinheiro(valor)}**.\n"
        f"📊 Novo total: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# REMOVER GASTO
# =========================================================

@tree.command(
    name="removergasto",
    description="Remove um gasto de uma favela"
)
@app_commands.describe(
    favela="Favela",
    valor="Valor a remover"
)
async def removergasto(
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    await interaction.response.defer(
        ephemeral=True
    )

    if favela not in FAVELAS:

        await interaction.followup.send(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.followup.send(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ O ranking ainda não foi criado.",
            ephemeral=True
        )

        return

    if dados[favela] < valor:

        await interaction.followup.send(
            f"❌ **{favela}** possui apenas "
            f"**{dinheiro(dados[favela])}**.",
            ephemeral=True
        )

        return

    dados[favela] -= valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar o ranking.",
            ephemeral=True
        )

        return

    await log_remover(
        interaction.user,
        favela,
        valor,
        dados[favela]
    )

    await interaction.followup.send(
        f"✅ Removido **{dinheiro(valor)}** da **{favela}**.\n"
        f"📊 Novo total: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# GASTO TOTAL
# =========================================================

@tree.command(
    name="gastototal",
    description="Mostra o total gasto por uma favela"
)
@app_commands.describe(
    favela="Favela"
)
async def gastototal(
    interaction: discord.Interaction,
    favela: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    if favela not in FAVELAS:

        await interaction.followup.send(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ O ranking ainda não foi criado.",
            ephemeral=True
        )

        return

    await interaction.followup.send(
        f"🏘️ **{favela}**\n"
        f"💰 Total gasto: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# ZERAR RANKING
# =========================================================

@tree.command(
    name="zerarranking",
    description="Zera todos os gastos do ranking"
)
async def zerarranking(
    interaction: discord.Interaction
):

    await interaction.response.defer(
        ephemeral=True
    )

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ O ranking ainda não foi criado.",
            ephemeral=True
        )

        return

    dados = novo_ranking()

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar o ranking.",
            ephemeral=True
        )

        return

    await log_geral(
        "🗑️ RANKING ZERADO",
        f"👤 Responsável: {interaction.user.mention}"
    )

    await interaction.followup.send(
        "✅ Todos os gastos foram zerados.",
        ephemeral=True
    )


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Bot online como {bot.user}"
    )

    try:

        await tree.sync()

        print(
            "✅ Comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"❌ Erro ao sincronizar comandos: {erro}"
        )

    try:

        await procurar_ranking()

        if ranking_message:

            print(
                "✅ Ranking encontrado."
            )

        else:

            print(
                "ℹ️ Nenhum ranking encontrado."
            )

    except Exception as erro:

        print(
            f"❌ Erro procurando ranking: {erro}"
        )


# =========================================================
# INICIAR
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "❌ DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
