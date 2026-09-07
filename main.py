import os
import base64
import json
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================================================
# WEBHOOKS
# =========================================================

WEBHOOK_ADICIONAR = "https://discord.com/api/webhooks/1546272715818672218/M2uvS74jTofIkxj_mkR70p-YaiTgYpmUHnYNnDe70NcrJCRoOlGDdinlQRDf7z_5Vt6T"
WEBHOOK_REMOVER = "https://discord.com/api/webhooks/1546273099987554389/j3yWVi6gLdx8saZKuoQ4L2MHe8BcoBaIHgzeQWSRALVfpBrcuYdX9YXR6uXWFi7ptoDd"
WEBHOOK_RANKING = "https://discord.com/api/webhooks/1546273377541423124/8M1YJqPtCkcZ-Z9RGfCMrRk0_7xFpufUBUoW5PH-KLGfDbLPstm-c7s8co3LKIUwD1gF"

# =========================================================
# FAVELAS
# =========================================================

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

# =========================================================
# BOT
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

ranking_message = None

# =========================================================
# PERMISSÕES
# =========================================================

permissoes = {
    "adicionar": set(),
    "remover": set(),
    "zerar": set(),
    "criar": set()
}

NOMES = {
    "adicionar": "➕ Adicionar gastos",
    "remover": "➖ Remover gastos",
    "zerar": "🗑️ Zerar ranking",
    "criar": "🏆 Criar ranking"
}


def tem_permissao(interaction, permissao):

    if interaction.guild is None:
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    return any(
        cargo.id in permissoes[permissao]
        for cargo in interaction.user.roles
    )


# =========================================================
# VALORES
# =========================================================

def dinheiro(valor):
    return f"R$ {valor:,}".replace(",", ".")


# =========================================================
# RANKING
# =========================================================

def novo_ranking():
    return {favela: 0 for favela in FAVELAS}


def codificar(dados):

    texto = json.dumps(
        dados,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return base64.urlsafe_b64encode(
        texto.encode("utf-8")
    ).decode("ascii")


def decodificar(codigo):

    try:

        texto = base64.urlsafe_b64decode(
            codigo.encode("ascii")
        ).decode("utf-8")

        dados = json.loads(texto)
        resultado = novo_ranking()

        for favela in FAVELAS:

            if favela in dados:
                resultado[favela] = int(dados[favela])

        return resultado

    except:

        return novo_ranking()


def criar_embed_ranking(dados):

    ordenado = sorted(
        dados.items(),
        key=lambda item: item[1],
        reverse=True
    )

    linhas = []

    for posicao, (favela, valor) in enumerate(
        ordenado,
        start=1
    ):

        if posicao == 1:
            prefixo = "🥇"
        elif posicao == 2:
            prefixo = "🥈"
        elif posicao == 3:
            prefixo = "🥉"
        else:
            prefixo = f"**{posicao}º**"

        linhas.append(
            f"{prefixo} **{favela}** — "
            f"**{dinheiro(valor)}**"
        )

    embed = discord.Embed(
        title="🏆 RANKING CAMPO BELO",
        description="\n".join(linhas),
        color=discord.Color.gold()
    )

    embed.set_author(
        name="Campo Belo",
        url=(
            "https://discord.com/"
            f"?cbdata={codificar(dados)}"
        )
    )

    embed.set_footer(
        text="Ranking atualizado automaticamente"
    )

    return embed


def ler_ranking(message):

    if not message.embeds:
        return None

    embed = message.embeds[0]

    if not embed.author:
        return None

    url = embed.author.url

    if not url:
        return None

    if "cbdata=" not in url:
        return None

    codigo = url.split(
        "cbdata=",
        1
    )[1]

    return decodificar(codigo)


async def procurar_ranking():

    global ranking_message

    if ranking_message:

        try:

            mensagem = await (
                ranking_message.channel.fetch_message(
                    ranking_message.id
                )
            )

            if ler_ranking(mensagem) is not None:

                ranking_message = mensagem

                return mensagem

        except:

            ranking_message = None

    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:

                async for mensagem in channel.history(
                    limit=100
                ):

                    if mensagem.author.id != bot.user.id:
                        continue

                    if not mensagem.embeds:
                        continue

                    embed = mensagem.embeds[0]

                    if embed.title != "🏆 RANKING CAMPO BELO":
                        continue

                    if ler_ranking(mensagem) is None:
                        continue

                    ranking_message = mensagem

                    return mensagem

            except Exception as erro:

                print(
                    f"Erro no canal {channel.name}: {erro}"
                )

    return None


async def carregar_ranking():

    mensagem = await procurar_ranking()

    if mensagem is None:
        return None

    return ler_ranking(mensagem)


async def atualizar_ranking(dados):

    global ranking_message

    if ranking_message is None:
        ranking_message = await procurar_ranking()

    if ranking_message is None:
        return False

    try:

        await ranking_message.edit(
            embed=criar_embed_ranking(dados)
        )

        return True

    except Exception as erro:

        print(
            f"Erro atualizando ranking: {erro}"
        )

        ranking_message = None

        return False


# =========================================================
# LOGS
# =========================================================

async def enviar_log(url, embed):

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
            f"❌ Erro enviando log: {erro}"
        )


# =========================================================
# /CRIARRANKING
# =========================================================

@tree.command(
    name="criarranking",
    description="Cria o ranking das favelas"
)
async def criarranking(interaction):

    if not tem_permissao(
        interaction,
        "criar"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para criar o ranking.",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    existente = await procurar_ranking()

    if existente:

        await interaction.followup.send(
            "⚠️ Já existe um ranking.",
            ephemeral=True
        )

        return

    global ranking_message

    ranking_message = await interaction.channel.send(
        embed=criar_embed_ranking(
            novo_ranking()
        )
    )

    # LOG RANKING
    embed_log = discord.Embed(
        title="🏆 RANKING CRIADO",
        color=discord.Color.blue()
    )

    embed_log.add_field(
        name="👤 Responsável",
        value=interaction.user.mention,
        inline=False
    )

    embed_log.add_field(
        name="📍 Canal",
        value=interaction.channel.mention,
        inline=False
    )

    await enviar_log(
        WEBHOOK_RANKING,
        embed_log
    )

    await interaction.followup.send(
        "✅ Ranking criado!",
        ephemeral=True
    )


# =========================================================
# /RANKING
# =========================================================

@tree.command(
    name="ranking",
    description="Mostra o ranking"
)
async def ranking(interaction):

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
        embed=criar_embed_ranking(dados),
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
    favela="Nome da favela",
    valor="Valor gasto"
)
async def adicionargasto(
    interaction,
    favela: str,
    valor: int
):

    if not tem_permissao(
        interaction,
        "adicionar"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para adicionar gastos.",
            ephemeral=True
        )

        return

    if favela not in FAVELAS:

        await interaction.response.send_message(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

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

    dados[favela] += valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar o ranking.",
            ephemeral=True
        )

        return

    # LOG ADICIONAR
    embed_log = discord.Embed(
        title="➕ GASTO ADICIONADO",
        color=discord.Color.green()
    )

    embed_log.add_field(
        name="👤 Responsável",
        value=interaction.user.mention,
        inline=False
    )

    embed_log.add_field(
        name="🏘️ Favela",
        value=favela,
        inline=True
    )

    embed_log.add_field(
        name="💰 Adicionado",
        value=f"+{dinheiro(valor)}",
        inline=True
    )

    embed_log.add_field(
        name="📊 Novo total",
        value=dinheiro(dados[favela]),
        inline=True
    )

    await enviar_log(
        WEBHOOK_ADICIONAR,
        embed_log
    )

    await interaction.followup.send(
        f"✅ **{favela}** recebeu "
        f"**{dinheiro(valor)}**.\n"
        f"📊 Total: **{dinheiro(dados[favela])}**",
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
    favela="Nome da favela",
    valor="Valor a remover"
)
async def removergasto(
    interaction,
    favela: str,
    valor: int
):

    if not tem_permissao(
        interaction,
        "remover"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para remover gastos.",
            ephemeral=True
        )

        return

    if favela not in FAVELAS:

        await interaction.response.send_message(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

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
            "❌ Não consegui atualizar.",
            ephemeral=True
        )

        return

    # LOG REMOVER
    embed_log = discord.Embed(
        title="➖ GASTO REMOVIDO",
        color=discord.Color.red()
    )

    embed_log.add_field(
        name="👤 Responsável",
        value=interaction.user.mention,
        inline=False
    )

    embed_log.add_field(
        name="🏘️ Favela",
        value=favela,
        inline=True
    )

    embed_log.add_field(
        name="💰 Removido",
        value=f"-{dinheiro(valor)}",
        inline=True
    )

    embed_log.add_field(
        name="📊 Novo total",
        value=dinheiro(dados[favela]),
        inline=True
    )

    await enviar_log(
        WEBHOOK_REMOVER,
        embed_log
    )

    await interaction.followup.send(
        f"✅ Removido **{dinheiro(valor)}** de **{favela}**.\n"
        f"📊 Total: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# /GASTOTOTAL
# =========================================================

@tree.command(
    name="gastototal",
    description="Mostra o total de uma favela"
)
@app_commands.describe(
    favela="Nome da favela"
)
async def gastototal(
    interaction,
    favela: str
):

    if favela not in FAVELAS:

        await interaction.response.send_message(
            "❌ Favela inválida.",
            ephemeral=True
        )

        return

    dados = await carregar_ranking()

    if dados is None:

        await interaction.response.send_message(
            "❌ Ranking não encontrado.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        f"🏘️ **{favela}**\n"
        f"💰 Total gasto: **{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# /ZERARRANKING
# =========================================================

@tree.command(
    name="zerarranking",
    description="Zera todo o ranking"
)
async def zerarranking(interaction):

    if not tem_permissao(
        interaction,
        "zerar"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para zerar o ranking.",
            ephemeral=True
        )

        return

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

    if not await atualizar_ranking(
        novo_ranking()
    ):

        await interaction.followup.send(
            "❌ Não consegui atualizar.",
            ephemeral=True
        )

        return

    # LOG RANKING
    embed_log = discord.Embed(
        title="🗑️ RANKING ZERADO",
        description=(
            f"👤 **Responsável:** "
            f"{interaction.user.mention}"
        ),
        color=discord.Color.red()
    )

    await enviar_log(
        WEBHOOK_RANKING,
        embed_log
    )

    await interaction.followup.send(
        "✅ Ranking zerado com sucesso.",
        ephemeral=True
    )


# =========================================================
# PAINEL DE PERMISSÕES
# =========================================================

class PermissaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label="Adicionar gastos",
                emoji="➕",
                value="adicionar"
            ),
            discord.SelectOption(
                label="Remover gastos",
                emoji="➖",
                value="remover"
            ),
            discord.SelectOption(
                label="Zerar ranking",
                emoji="🗑️",
                value="zerar"
            ),
            discord.SelectOption(
                label="Criar ranking",
                emoji="🏆",
                value="criar"
            )
        ]

        super().__init__(
            placeholder="🔐 Escolha uma permissão",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores podem configurar permissões.",
                ephemeral=True
            )

            return

        permissao = self.values[0]

        await interaction.response.send_message(
            f"🔐 **{NOMES[permissao]}**\n\n"
            "Agora escolha o cargo:",
            view=EscolherCargoView(permissao),
            ephemeral=True
        )


class EscolherCargoSelect(discord.ui.RoleSelect):

    def __init__(self, permissao):

        super().__init__(
            placeholder="👤 Escolha um cargo",
            min_values=1,
            max_values=1
        )

        self.permissao = permissao

    async def callback(self, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores podem fazer isso.",
                ephemeral=True
            )

            return

        cargo = self.values[0]

        permissoes[
            self.permissao
        ].add(cargo.id)

        await interaction.response.send_message(
            "✅ **Permissão adicionada!**\n\n"
            f"👤 Cargo: {cargo.mention}\n"
            f"🔐 Permissão: **{NOMES[self.permissao]}**",
            ephemeral=True
        )


class EscolherCargoView(discord.ui.View):

    def __init__(self, permissao):

        super().__init__(timeout=120)

        self.add_item(
            EscolherCargoSelect(permissao)
        )


class RemoverPermissaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label="Adicionar gastos",
                emoji="➕",
                value="adicionar"
            ),
            discord.SelectOption(
                label="Remover gastos",
                emoji="➖",
                value="remover"
            ),
            discord.SelectOption(
                label="Zerar ranking",
                emoji="🗑️",
                value="zerar"
            ),
            discord.SelectOption(
                label="Criar ranking",
                emoji="🏆",
                value="criar"
            )
        ]

        super().__init__(
            placeholder="🗑️ Escolha a permissão",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores podem configurar permissões.",
                ephemeral=True
            )

            return

        permissao = self.values[0]

        await interaction.response.send_message(
            "🗑️ Escolha o cargo:",
            view=RemoverCargoView(permissao),
            ephemeral=True
        )


class RemoverCargoSelect(discord.ui.RoleSelect):

    def __init__(self, permissao):

        super().__init__(
            placeholder="👤 Escolha um cargo",
            min_values=1,
            max_values=1
        )

        self.permissao = permissao

    async def callback(self, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores podem fazer isso.",
                ephemeral=True
            )

            return

        cargo = self.values[0]

        permissoes[
            self.permissao
        ].discard(cargo.id)

        await interaction.response.send_message(
            "✅ **Permissão removida!**\n\n"
            f"👤 Cargo: {cargo.mention}\n"
            f"🔐 Permissão: **{NOMES[self.permissao]}**",
            ephemeral=True
        )


class RemoverCargoView(discord.ui.View):

    def __init__(self, permissao):

        super().__init__(timeout=120)

        self.add_item(
            RemoverCargoSelect(permissao)
        )


async def mostrar_permissoes(guild):

    texto = ""

    for permissao, cargos in permissoes.items():

        texto += f"\n{NOMES[permissao]}\n"

        validos = []

        for cargo_id in cargos:

            cargo = guild.get_role(cargo_id)

            if cargo:
                validos.append(cargo.mention)

        if validos:

            texto += "\n".join(
                f"• {cargo}"
                for cargo in validos
            )

        else:

            texto += "• Nenhum cargo configurado."

        texto += "\n"

    return texto


class PainelPermissoesView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(
        label="Adicionar permissão",
        emoji="➕",
        style=discord.ButtonStyle.success,
        custom_id="campo_belo_perm_add"
    )
    async def adicionar(self, interaction, button):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔐 Escolha a permissão:",
            view=PermissaoView(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Remover permissão",
        emoji="➖",
        style=discord.ButtonStyle.danger,
        custom_id="campo_belo_perm_remove"
    )
    async def remover(self, interaction, button):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🗑️ Escolha a permissão:",
            view=RemoverPermissaoView(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Ver permissões",
        emoji="📋",
        style=discord.ButtonStyle.primary,
        custom_id="campo_belo_perm_view"
    )
    async def ver(self, interaction, button):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Apenas administradores.",
                ephemeral=True
            )

            return

        texto = await mostrar_permissoes(
            interaction.guild
        )

        embed = discord.Embed(
            title="📋 PERMISSÕES CAMPO BELO",
            description=texto,
            color=discord.Color.blue()
        )

        embed.set_footer(
            text="Administradores possuem acesso total."
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class PermissaoView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=120)

        self.add_item(
            PermissaoSelect()
        )


class RemoverPermissaoView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=120)

        self.add_item(
            RemoverPermissaoSelect()
        )


# =========================================================
# /PAINELPERMISSOES
# =========================================================

@tree.command(
    name="painelpermissoes",
    description="Cria o painel de permissões"
)
async def painelpermissoes(interaction):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ Apenas administradores podem criar o painel.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="⚙️ CONFIGURAÇÃO DE PERMISSÕES",
        description=(
            "Configure os cargos que podem controlar o ranking.\n\n"
            "➕ **Adicionar permissão**\n"
            "Libera uma função para um cargo.\n\n"
            "➖ **Remover permissão**\n"
            "Retira uma função de um cargo.\n\n"
            "📋 **Ver permissões**\n"
            "Mostra os cargos configurados."
        ),
        color=discord.Color.gold()
    )

    await interaction.channel.send(
        embed=embed,
        view=PainelPermissoesView()
    )

    await interaction.response.send_message(
        "✅ Painel criado!",
        ephemeral=True
    )


# =========================================================
# ERROS
# =========================================================

@bot.event
async def on_app_command_error(
    interaction,
    error
):

    print(f"❌ Erro: {error}")

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
            print("✅ Ranking encontrado.")
        else:
            print("ℹ️ Nenhum ranking encontrado.")

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
