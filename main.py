import os
import base64
import json
import discord
from discord import app_commands

# =========================================================
# CONFIGURAÇÃO
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# COLOQUE SEUS 3 NOVOS WEBHOOKS AQUI
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

MARCADOR = "CAMPO_BELO_RANKING"

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

ranking_message = None


# =========================================================
# DADOS
# =========================================================

def novo_ranking():
    return {favela: 0 for favela in FAVELAS}


def dinheiro(valor):
    return f"R$ {valor:,}".replace(",", ".")


def codificar_dados(dados):
    """
    Converte os valores do ranking para texto codificado.
    Isso fica escondido na URL do autor do embed.
    """
    texto = json.dumps(
        dados,
        ensure_ascii=False,
        separators=(",", ":")
    )

    codificado = base64.urlsafe_b64encode(
        texto.encode("utf-8")
    ).decode("ascii")

    return codificado


def decodificar_dados(codificado):
    try:
        texto = base64.urlsafe_b64decode(
            codificado.encode("ascii")
        ).decode("utf-8")

        dados = json.loads(texto)

        resultado = novo_ranking()

        for favela in FAVELAS:
            if favela in dados:
                resultado[favela] = int(dados[favela])

        return resultado

    except Exception as erro:
        print(f"Erro ao decodificar ranking: {erro}")
        return novo_ranking()


# =========================================================
# EMBED DO RANKING
# =========================================================

def criar_embed(dados):

    ordenado = sorted(
        dados.items(),
        key=lambda item: item[1],
        reverse=True
    )

    linhas = []

    for posicao, (favela, valor) in enumerate(ordenado, start=1):

        if posicao == 1:
            prefixo = "🥇"
        elif posicao == 2:
            prefixo = "🥈"
        elif posicao == 3:
            prefixo = "🥉"
        else:
            prefixo = f"**{posicao}º**"

        linhas.append(
            f"{prefixo} **{favela}** — **{dinheiro(valor)}**"
        )

    embed = discord.Embed(
        title="🏆 RANKING CAMPO BELO",
        description="\n".join(linhas),
        color=discord.Color.gold()
    )

    # Os dados ficam codificados na URL do autor.
    # NÃO aparecem como texto no ranking.
    dados_codificados = codificar_dados(dados)

    embed.set_author(
        name="Campo Belo",
        url=f"https://discord.com/?cbdata={dados_codificados}"
    )

    embed.set_footer(
        text="Ranking atualizado automaticamente"
    )

    return embed


def ler_dados(message):

    if not message.embeds:
        return None

    embed = message.embeds[0]

    if not embed.author:
        return None

    url = embed.author.url

    if not url:
        return None

    marcador = "cbdata="

    if marcador not in url:
        return None

    codificado = url.split(
        marcador,
        1
    )[1]

    return decodificar_dados(codificado)


# =========================================================
# PROCURAR RANKING
# =========================================================

async def procurar_ranking():

    global ranking_message

    # Primeiro tenta a mensagem já conhecida
    if ranking_message is not None:

        try:

            mensagem = await ranking_message.channel.fetch_message(
                ranking_message.id
            )

            dados = ler_dados(mensagem)

            if dados is not None:
                ranking_message = mensagem
                return mensagem

        except Exception:
            ranking_message = None

    # Procura nos canais
    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                async for message in channel.history(limit=100):

                    if bot.user is None:
                        continue

                    if message.author.id != bot.user.id:
                        continue

                    if not message.embeds:
                        continue

                    embed = message.embeds[0]

                    if embed.title != "🏆 RANKING CAMPO BELO":
                        continue

                    dados = ler_dados(message)

                    if dados is None:
                        continue

                    ranking_message = message

                    print(
                        f"Ranking encontrado em #{channel.name}"
                    )

                    return message

            except Exception as erro:

                print(
                    f"Erro procurando no canal {channel.name}: {erro}"
                )

    return None


# =========================================================
# CARREGAR RANKING
# =========================================================

async def carregar_ranking():

    message = await procurar_ranking()

    if message is None:
        return None

    return ler_dados(message)


# =========================================================
# ATUALIZAR RANKING
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
            session=bot.http._HTTPClient__session
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


# =========================================================
# LOG GERAL
# =========================================================

async def log_geral(titulo, descricao):

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
# /CRIARRANKING
# =========================================================

@tree.command(
    name="criarranking",
    description="Cria o ranking das favelas"
)
async def criarranking(interaction: discord.Interaction):

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
# /RANKING
# =========================================================

@tree.command(
    name="ranking",
    description="Mostra o ranking atual"
)
async def ranking(interaction: discord.Interaction):

    await interaction.response.defer(
        ephemeral=True
    )

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ Ranking não encontrado. Use /criarranking.",
            ephemeral=True
        )

        return

    await interaction.followup.send(
        embed=criar_embed(dados),
        ephemeral=True
    )


# =========================================================
# /ADICIONARGASTO
# =========================================================

@tree.command(
    name="adicionargasto",
    description="Adiciona gasto para uma favela"
)
@app_commands.describe(
    favela="Favela",
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
            "❌ Ranking não encontrado. Use /criarranking.",
            ephemeral=True
        )

        return

    dados[favela] += valor

    if not await atualizar_ranking(dados):

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
# /REMOVERGASTO
# =========================================================

@tree.command(
    name="removergasto",
    description="Remove gasto de uma favela"
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
            "❌ Ranking não encontrado.",
            ephemeral=True
        )

        return

    if dados[favela] < valor:

        await interaction.followup.send(
            f"❌ **{favela}** tem apenas "
            f"**{dinheiro(dados[favela])}**.",
            ephemeral=True
        )

        return

    dados[favela] -= valor

    if not await atualizar_ranking(dados):

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
# /GASTOTOTAL
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
            "❌ Ranking não encontrado.",
            ephemeral=True
        )

        return

    await interaction.followup.send(
        f"🏘️ **{favela}**\n"
        f"💰 Total gasto: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# /ZERARRANKING
# =========================================================

@tree.command(
    name="zerarranking",
    description="Zera todos os gastos"
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
            "❌ Ranking não encontrado.",
            ephemeral=True
        )

        return

    dados = novo_ranking()

    if not await atualizar_ranking(dados):

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
# ERROS DOS COMANDOS
# =========================================================

@bot.event
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    print(
        f"Erro no comando: {error}"
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                "❌ Ocorreu um erro ao executar o comando.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "❌ Ocorreu um erro ao executar o comando.",
                ephemeral=True
            )

    except:
        pass


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Bot online: {bot.user}"
    )

    try:

        await tree.sync()

        print(
            "✅ Comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"❌ Erro sincronizando comandos: {erro}"
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
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
