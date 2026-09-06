import os
import asyncio
import discord
from discord import app_commands

# =========================
# CONFIGURAÇÕES
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

# COLOQUE AQUI OS 3 NOVOS WEBHOOKS
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

MARKER = "CAMPO_BELO_RANKING_V1"

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Guarda a mensagem do ranking em memória
ranking_message = None
ranking_channel_id = None
ranking_message_id = None


# =========================
# DADOS
# =========================

def novo_ranking():
    return {favela: 0 for favela in FAVELAS}


def dinheiro(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")


def criar_embed(dados):
    ordenado = sorted(
        dados.items(),
        key=lambda x: x[1],
        reverse=True
    )

    descricao = ""

    for posicao, (favela, valor) in enumerate(ordenado, start=1):
        if posicao == 1:
            emoji = "🥇"
        elif posicao == 2:
            emoji = "🥈"
        elif posicao == 3:
            emoji = "🥉"
        else:
            emoji = f"**{posicao}º**"

        descricao += f"{emoji} **{favela}** — {dinheiro(valor)}\n"

    embed = discord.Embed(
        title="🏆 RANKING CAMPO BELO",
        description=descricao,
        color=discord.Color.gold()
    )

    embed.set_footer(text=MARKER)

    return embed


def ler_ranking_da_mensagem(message):
    dados = novo_ranking()

    if not message.embeds:
        return dados

    embed = message.embeds[0]

    if not embed.description:
        return dados

    linhas = embed.description.split("\n")

    for linha in linhas:
        for favela in FAVELAS:
            if f"**{favela}**" in linha:
                try:
                    parte = linha.split("—")[1]
                    numero = (
                        parte
                        .replace("R$", "")
                        .replace(".", "")
                        .replace(",", "")
                        .strip()
                    )

                    dados[favela] = int(numero)
                except:
                    pass

    return dados


# =========================
# PROCURAR RANKING
# =========================

async def procurar_ranking():
    global ranking_message
    global ranking_channel_id
    global ranking_message_id

    for guild in bot.guilds:
        for channel in guild.text_channels:

            try:
                async for message in channel.history(limit=100):
                    if message.author.id != bot.user.id:
                        continue

                    if not message.embeds:
                        continue

                    embed = message.embeds[0]

                    if embed.footer and embed.footer.text == MARKER:
                        ranking_message = message
                        ranking_channel_id = channel.id
                        ranking_message_id = message.id

                        return message

            except:
                continue

    return None


# =========================
# CARREGAR RANKING
# =========================

async def carregar_ranking():
    global ranking_message

    if ranking_message is not None:
        try:
            await ranking_message.fetch()
            return ler_ranking_da_mensagem(ranking_message)
        except:
            ranking_message = None

    message = await procurar_ranking()

    if message:
        return ler_ranking_da_mensagem(message)

    return novo_ranking()


# =========================
# ATUALIZAR RANKING
# =========================

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
    except:
        return False


# =========================
# WEBHOOK
# =========================

async def enviar_webhook(url, embed):
    if not url or url.startswith("COLE_AQUI"):
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
        print(f"Erro no webhook: {erro}")


# =========================
# LOG ADICIONAR
# =========================

async def log_adicionar(usuario, favela, valor, total):
    embed = discord.Embed(
        title="➕ GASTO ADICIONADO",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Quem adicionou",
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


# =========================
# LOG REMOVER
# =========================

async def log_remover(usuario, favela, valor, total):
    embed = discord.Embed(
        title="➖ GASTO REMOVIDO",
        color=discord.Color.red()
    )

    embed.add_field(
        name="👤 Quem removeu",
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


# =========================
# LOG GERAL
# =========================

async def log_ranking(titulo, descricao):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=discord.Color.blue()
    )

    await enviar_webhook(
        WEBHOOK_RANKING,
        embed
    )


# =========================
# /CRIARRANKING
# =========================

@tree.command(
    name="criarranking",
    description="Cria o ranking das favelas"
)
async def criarranking(interaction: discord.Interaction):

    global ranking_message
    global ranking_channel_id
    global ranking_message_id

    await interaction.response.defer(ephemeral=True)

    existente = await procurar_ranking()

    if existente:
        await interaction.followup.send(
            "⚠️ Já existe um ranking neste servidor.",
            ephemeral=True
        )
        return

    dados = novo_ranking()

    message = await interaction.channel.send(
        embed=criar_embed(dados)
    )

    ranking_message = message
    ranking_channel_id = message.channel.id
    ranking_message_id = message.id

    await log_ranking(
        "🏆 RANKING CRIADO",
        f"👤 Criado por: {interaction.user.mention}\n"
        f"📍 Canal: {interaction.channel.mention}"
    )

    await interaction.followup.send(
        "✅ Ranking criado com sucesso!",
        ephemeral=True
    )


# =========================
# /RANKING
# =========================

@tree.command(
    name="ranking",
    description="Mostra o ranking atual"
)
async def ranking(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    dados = await carregar_ranking()

    ordenado = sorted(
        dados.items(),
        key=lambda x: x[1],
        reverse=True
    )

    texto = ""

    for posicao, (favela, valor) in enumerate(ordenado, start=1):
        texto += f"**{posicao}º — {favela}**: {dinheiro(valor)}\n"

    embed = discord.Embed(
        title="🏆 RANKING CAMPO BELO",
        description=texto,
        color=discord.Color.gold()
    )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True
    )


# =========================
# /ADICIONARGASTO
# =========================

@tree.command(
    name="adicionargasto",
    description="Adiciona dinheiro gasto por uma favela"
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

    await interaction.response.defer(ephemeral=True)

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

    dados[favela] += valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:
        await interaction.followup.send(
            "❌ Não encontrei a mensagem do ranking. Use `/criarranking` primeiro.",
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


# =========================
# /REMOVERGASTO
# =========================

@tree.command(
    name="removergasto",
    description="Remove dinheiro gasto de uma favela"
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

    await interaction.response.defer(ephemeral=True)

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

    if valor > dados[favela]:
        await interaction.followup.send(
            f"❌ A **{favela}** não possui esse valor para remover.",
            ephemeral=True
        )
        return

    dados[favela] -= valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:
        await interaction.followup.send(
            "❌ Não encontrei a mensagem do ranking.",
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


# =========================
# /GASTOTOTAL
# =========================

@tree.command(
    name="gastototal",
    description="Mostra quanto uma favela já gastou"
)
@app_commands.describe(
    favela="Favela"
)
async def gastototal(
    interaction: discord.Interaction,
    favela: str
):

    await interaction.response.defer(ephemeral=True)

    if favela not in FAVELAS:
        await interaction.followup.send(
            "❌ Favela inválida.",
            ephemeral=True
        )
        return

    dados = await carregar_ranking()

    await interaction.followup.send(
        f"🏘️ **{favela}**\n"
        f"💰 Total gasto: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================
# /ZERARRANKING
# =========================

@tree.command(
    name="zerarranking",
    description="Zera todos os gastos do ranking"
)
async def zerarranking(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    dados = novo_ranking()

    sucesso = await atualizar_ranking(dados)

    if not sucesso:
        await interaction.followup.send(
            "❌ Não encontrei a mensagem do ranking.",
            ephemeral=True
        )
        return

    await log_ranking(
        "🗑️ RANKING ZERADO",
        f"👤 Quem zerou: {interaction.user.mention}"
    )

    await interaction.followup.send(
        "✅ Todos os gastos foram zerados.",
        ephemeral=True
    )


# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():

    global ranking_message

    try:
        await tree.sync()
        print("Comandos sincronizados.")
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")

    try:
        ranking_message = await procurar_ranking()
    except Exception as erro:
        print(f"Erro ao procurar ranking: {erro}")

    print(f"Bot online como {bot.user}")


# =========================
# INICIAR
# =========================

if not TOKEN:
    raise RuntimeError(
        "A variável DISCORD_TOKEN não foi configurada."
    )

bot.run(TOKEN)
