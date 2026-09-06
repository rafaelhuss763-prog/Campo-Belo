import discord
from discord import app_commands
import re
import os

# ============================================================
# CAMPO BELO — RANKING + 3 WEBHOOKS
# ============================================================

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

# ============================================================
# COLOQUE OS 3 WEBHOOKS AQUI
# ============================================================

WEBHOOK_ADICIONAR = "https://discord.com/api/webhooks/1546272715818672218/M2uvS74jTofIkxj_mkR70p-YaiTgYpmUHnYNnDe70NcrJCRoOlGDdinlQRDf7z_5Vt6T"

WEBHOOK_REMOVER = "https://discord.com/api/webhooks/1546273099987554389/j3yWVi6gLdx8saZKuoQ4L2MHe8BcoBaIHgzeQWSRALVfpBrcuYdX9YXR6uXWFi7ptoDd"

WEBHOOK_RANKING = "https://discord.com/api/webhooks/1546273377541423124/8M1YJqPtCkcZ-Z9RGfCMrRk0_7xFpufUBUoW5PH-KLGfDbLPstm-c7s8co3LKIUwD1gF"


# Identificação da mensagem oficial do ranking
MARKER = "CAMPO_BELO_RANKING_V1"


# ============================================================
# CONFIGURAÇÃO DO BOT
# ============================================================

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# ============================================================
# FUNÇÕES DO RANKING
# ============================================================

def novo_ranking():
    return {
        favela: 0
        for favela in FAVELAS
    }


def dinheiro(valor):
    return f"${valor:,}".replace(",", ".")


def criar_embed(ranking):

    ordenado = sorted(
        ranking.items(),
        key=lambda item: item[1],
        reverse=True
    )

    medalhas = [
        "🥇",
        "🥈",
        "🥉"
    ]

    linhas = []

    for posicao, (favela, valor) in enumerate(
        ordenado,
        start=1
    ):

        if posicao <= 3 and valor > 0:
            prefixo = medalhas[posicao - 1]
        else:
            prefixo = f"**{posicao}º**"

        linhas.append(
            f"{prefixo} **{favela}** — `{dinheiro(valor)}`"
        )

    embed = discord.Embed(
        title="🏆 RANKING — CAMPO BELO",
        description=(
            "💰 **Ranking por total gasto**\n\n"
            + "\n".join(linhas)
        )
    )

    embed.set_footer(
        text=MARKER
    )

    return embed


def ler_ranking_da_mensagem(message):

    ranking = novo_ranking()

    if not message.embeds:
        return ranking

    embed = message.embeds[0]

    if not embed.description:
        return ranking

    for linha in embed.description.splitlines():

        for favela in FAVELAS:

            if f"**{favela}**" in linha:

                parte = linha.split(
                    f"**{favela}**",
                    1
                )[1]

                numeros = re.search(
                    r"\$([\d.]+)",
                    parte
                )

                if numeros:

                    ranking[favela] = int(
                        numeros.group(1).replace(
                            ".",
                            ""
                        )
                    )

                break

    return ranking


# ============================================================
# PROCURAR MENSAGEM DO RANKING
# ============================================================

async def procurar_ranking():

    if bot.user is None:
        return None

    for guild in bot.guilds:

        for canal in guild.text_channels:

            try:

                async for mensagem in canal.history(
                    limit=100
                ):

                    if mensagem.author.id != bot.user.id:
                        continue

                    if not mensagem.embeds:
                        continue

                    footer = mensagem.embeds[0].footer

                    if (
                        footer
                        and footer.text == MARKER
                    ):
                        return mensagem

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue

    return None


# ============================================================
# CARREGAR RANKING
# ============================================================

async def carregar_ranking():

    mensagem = await procurar_ranking()

    if mensagem:

        return ler_ranking_da_mensagem(
            mensagem
        )

    return novo_ranking()


# ============================================================
# ATUALIZAR RANKING
# ============================================================

async def atualizar_ranking(ranking):

    mensagem = await procurar_ranking()

    if not mensagem:
        return False

    try:

        await mensagem.edit(
            embed=criar_embed(ranking)
        )

        return True

    except (
        discord.Forbidden,
        discord.HTTPException
    ):
        return False


# ============================================================
# ENVIAR WEBHOOK
# ============================================================

async def enviar_webhook(
    url,
    titulo,
    descricao,
    cor=0x2ECC71
):

    if not url:
        return

    if url.startswith("COLE_AQUI"):
        return

    try:

        webhook = discord.Webhook.from_url(
            url,
            client=bot
        )

        embed = discord.Embed(
            title=titulo,
            description=descricao,
            color=cor
        )

        await webhook.send(
            embed=embed,
            username="Campo Belo Logs",
            wait=False
        )

    except Exception as erro:

        print(
            "Erro no webhook:",
            repr(erro)
        )


# ============================================================
# LOG — ADICIONAR GASTO
# ============================================================

async def log_adicionar(
    interaction,
    favela,
    valor,
    novo_total
):

    descricao = (
        f"👤 **Quem adicionou:** "
        f"{interaction.user.mention}\n\n"

        f"🏘️ **Favela:** "
        f"**{favela}**\n\n"

        f"💰 **Valor adicionado:** "
        f"**{dinheiro(valor)}**\n\n"

        f"💵 **Novo total:** "
        f"**{dinheiro(novo_total)}**"
    )

    await enviar_webhook(
        WEBHOOK_ADICIONAR,
        "🟢 VALOR ADICIONADO",
        descricao,
        0x2ECC71
    )


# ============================================================
# LOG — REMOVER GASTO
# ============================================================

async def log_remover(
    interaction,
    favela,
    valor,
    novo_total
):

    descricao = (
        f"👤 **Quem removeu:** "
        f"{interaction.user.mention}\n\n"

        f"🏘️ **Favela:** "
        f"**{favela}**\n\n"

        f"💰 **Valor removido:** "
        f"**{dinheiro(valor)}**\n\n"

        f"💵 **Novo total:** "
        f"**{dinheiro(novo_total)}**"
    )

    await enviar_webhook(
        WEBHOOK_REMOVER,
        "🔴 VALOR REMOVIDO",
        descricao,
        0xE74C3C
    )


# ============================================================
# LOG — RANKING
# ============================================================

async def log_ranking(
    interaction,
    acao
):

    descricao = (
        f"👤 **Responsável:** "
        f"{interaction.user.mention}\n\n"

        f"📋 **Ação:** "
        f"**{acao}**"
    )

    await enviar_webhook(
        WEBHOOK_RANKING,
        "🏆 LOG DO RANKING",
        descricao,
        0x3498DB
    )


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    try:

        await tree.sync()

        print(
            f"Bot online como {bot.user}"
        )

        print(
            "Comandos sincronizados."
        )

    except Exception as erro:

        print(
            "Erro ao sincronizar:",
            repr(erro)
        )


# ============================================================
# CRIAR RANKING
# ============================================================

@tree.command(
    name="criarranking",
    description="Cria o ranking fixo neste canal"
)
async def criarranking(
    interaction: discord.Interaction
):

    existente = await procurar_ranking()

    if existente:

        await interaction.response.send_message(
            "⚠️ Já existe um ranking fixo.",
            ephemeral=True
        )

        return

    ranking = novo_ranking()

    try:

        await interaction.channel.send(
            embed=criar_embed(ranking)
        )

        await log_ranking(
            interaction,
            "Ranking criado"
        )

        await interaction.response.send_message(
            "✅ Ranking criado com sucesso!",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Não tenho permissão para enviar mensagens aqui.",
            ephemeral=True
        )


# ============================================================
# RANKING
# ============================================================

@tree.command(
    name="ranking",
    description="Mostra o ranking atual"
)
async def ranking(
    interaction: discord.Interaction
):

    dados = await carregar_ranking()

    await interaction.response.send_message(
        embed=criar_embed(dados)
    )


# ============================================================
# ADICIONAR GASTO
# ============================================================

@tree.command(
    name="adicionargasto",
    description="Adiciona um valor para uma favela"
)
@app_commands.describe(
    favela="Favela que fez a compra",
    valor="Valor gasto"
)
@app_commands.choices(
    favela=[
        app_commands.Choice(
            name=favela,
            value=favela
        )
        for favela in FAVELAS
    ]
)
async def adicionargasto(
    interaction: discord.Interaction,
    favela: app_commands.Choice[str],
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    nome = favela.value

    dados[nome] += valor

    atualizado = await atualizar_ranking(
        dados
    )

    if not atualizado:

        await interaction.response.send_message(
            "❌ Primeiro use `/criarranking`.",
            ephemeral=True
        )

        return

    # LOG
    await log_adicionar(
        interaction,
        nome,
        valor,
        dados[nome]
    )

    await interaction.response.send_message(
        f"✅ **{nome}** recebeu "
        f"**+{dinheiro(valor)}**.\n"
        f"💰 Novo total: "
        f"**{dinheiro(dados[nome])}**"
    )


# ============================================================
# REMOVER GASTO
# ============================================================

@tree.command(
    name="removergasto",
    description="Remove um valor de uma favela"
)
@app_commands.describe(
    favela="Favela",
    valor="Valor que será removido"
)
@app_commands.choices(
    favela=[
        app_commands.Choice(
            name=favela,
            value=favela
        )
        for favela in FAVELAS
    ]
)
async def removergasto(
    interaction: discord.Interaction,
    favela: app_commands.Choice[str],
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    nome = favela.value

    dados[nome] = max(
        0,
        dados[nome] - valor
    )

    atualizado = await atualizar_ranking(
        dados
    )

    if not atualizado:

        await interaction.response.send_message(
            "❌ Primeiro use `/criarranking`.",
            ephemeral=True
        )

        return

    # LOG
    await log_remover(
        interaction,
        nome,
        valor,
        dados[nome]
    )

    await interaction.response.send_message(
        f"✅ Removido "
        f"**{dinheiro(valor)}** de **{nome}**.\n"
        f"💰 Novo total: "
        f"**{dinheiro(dados[nome])}**"
    )


# ============================================================
# CONSULTAR TOTAL
# ============================================================

@tree.command(
    name="gastototal",
    description="Consulta quanto uma favela gastou"
)
@app_commands.describe(
    favela="Favela para consultar"
)
@app_commands.choices(
    favela=[
        app_commands.Choice(
            name=favela,
            value=favela
        )
        for favela in FAVELAS
    ]
)
async def gastototal(
    interaction: discord.Interaction,
    favela: app_commands.Choice[str]
):

    dados = await carregar_ranking()

    nome = favela.value

    await interaction.response.send_message(
        f"💰 **{nome}** já gastou "
        f"**{dinheiro(dados[nome])}**.",
        ephemeral=True
    )


# ============================================================
# ZERAR RANKING
# ============================================================

@tree.command(
    name="zerarranking",
    description="Zera todos os valores do ranking"
)
async def zerarranking(
    interaction: discord.Interaction
):

    dados = novo_ranking()

    atualizado = await atualizar_ranking(
        dados
    )

    if not atualizado:

        await interaction.response.send_message(
            "❌ Primeiro use `/criarranking`.",
            ephemeral=True
        )

        return

    await log_ranking(
        interaction,
        "Ranking zerado"
    )

    await interaction.response.send_message(
        "✅ Ranking zerado com sucesso."
    )


# ============================================================
# ERROS
# ============================================================

@bot.event
async def on_app_command_error(
    interaction,
    error
):

    print(
        "ERRO:",
        repr(error)
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

    except discord.HTTPException:
        pass


# ============================================================
# TOKEN DO TEMALIX
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:

    raise RuntimeError(
        "A variável DISCORD_TOKEN não foi configurada no Temalix."
    )

bot.run(TOKEN)
