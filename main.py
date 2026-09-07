import os
import base64
import json
import discord
from discord import app_commands

# =========================================================
# CONFIGURAÇÃO
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

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

permissoes_cargos = {
    "adicionar": set(),
    "remover": set(),
    "zerar": set(),
    "criar_ranking": set()
}

NOMES_PERMISSOES = {
    "adicionar": "➕ Adicionar gastos",
    "remover": "➖ Remover gastos",
    "zerar": "🗑️ Zerar ranking",
    "criar_ranking": "🏆 Criar ranking"
}

# =========================================================
# UTILIDADES
# =========================================================

def dinheiro(valor):
    return f"R$ {valor:,}".replace(",", ".")


def possui_permissao(interaction, permissao):
    if interaction.guild is None:
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    return any(
        cargo.id in permissoes_cargos[permissao]
        for cargo in interaction.user.roles
    )


# =========================================================
# RANKING
# =========================================================

def novo_ranking():
    return {
        favela: 0
        for favela in FAVELAS
    }


def codificar_dados(dados):
    texto = json.dumps(
        dados,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return base64.urlsafe_b64encode(
        texto.encode("utf-8")
    ).decode("ascii")


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
        print(f"Erro decodificando ranking: {erro}")
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

    dados_codificados = codificar_dados(dados)

    embed.set_author(
        name="Campo Belo",
        url=(
            "https://discord.com/"
            f"?cbdata={dados_codificados}"
        )
    )

    embed.set_footer(
        text="Ranking atualizado automaticamente"
    )

    return embed


def ler_dados_ranking(message):
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

    codificado = url.split(
        "cbdata=",
        1
    )[1]

    return decodificar_dados(codificado)


async def procurar_ranking():
    global ranking_message

    if ranking_message:
        try:
            mensagem = await (
                ranking_message.channel.fetch_message(
                    ranking_message.id
                )
            )

            dados = ler_dados_ranking(mensagem)

            if dados is not None:
                ranking_message = mensagem
                return mensagem

        except Exception:
            ranking_message = None

    for guild in bot.guilds:

        for channel in guild.text_channels:

            try:
                async for message in channel.history(
                    limit=100
                ):

                    if not bot.user:
                        continue

                    if message.author.id != bot.user.id:
                        continue

                    if not message.embeds:
                        continue

                    embed = message.embeds[0]

                    if embed.title != "🏆 RANKING CAMPO BELO":
                        continue

                    dados = ler_dados_ranking(message)

                    if dados is None:
                        continue

                    ranking_message = message

                    return message

            except Exception as erro:
                print(
                    f"Erro no canal "
                    f"{channel.name}: {erro}"
                )

    return None


async def carregar_ranking():
    mensagem = await procurar_ranking()

    if mensagem is None:
        return None

    return ler_dados_ranking(mensagem)


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
# PAINEL DE PERMISSÕES
# =========================================================

class PermissaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label="Adicionar gastos",
                description="Permite usar /adicionargasto",
                emoji="➕",
                value="adicionar"
            ),
            discord.SelectOption(
                label="Remover gastos",
                description="Permite usar /removergasto",
                emoji="➖",
                value="remover"
            ),
            discord.SelectOption(
                label="Zerar ranking",
                description="Permite usar /zerarranking",
                emoji="🗑️",
                value="zerar"
            ),
            discord.SelectOption(
                label="Criar ranking",
                description="Permite usar /criarranking",
                emoji="🏆",
                value="criar_ranking"
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
            f"🔐 Permissão selecionada:\n"
            f"**{NOMES_PERMISSOES[permissao]}**\n\n"
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

        permissoes_cargos[
            self.permissao
        ].add(cargo.id)

        await interaction.response.send_message(
            "✅ **Permissão adicionada!**\n\n"
            f"👤 Cargo: {cargo.mention}\n"
            f"🔐 Permissão: "
            f"**{NOMES_PERMISSOES[self.permissao]}**",
            ephemeral=True
        )


class EscolherCargoView(discord.ui.View):

    def __init__(self, permissao):

        super().__init__(timeout=120)

        self.add_item(
            EscolherCargoSelect(permissao)
        )


# =========================================================
# REMOVER PERMISSÃO
# =========================================================

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
                value="criar_ranking"
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
            "🗑️ Escolha o cargo que perderá a permissão:",
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

        permissoes_cargos[
            self.permissao
        ].discard(cargo.id)

        await interaction.response.send_message(
            "✅ **Permissão removida!**\n\n"
            f"👤 Cargo: {cargo.mention}\n"
            f"🔐 Permissão: "
            f"**{NOMES_PERMISSOES[self.permissao]}**",
            ephemeral=True
        )


class RemoverCargoView(discord.ui.View):

    def __init__(self, permissao):

        super().__init__(timeout=120)

        self.add_item(
            RemoverCargoSelect(permissao)
        )


# =========================================================
# VER PERMISSÕES
# =========================================================

async def criar_lista_permissoes(guild):

    texto = ""

    for permissao, cargos in permissoes_cargos.items():

        texto += (
            f"\n{NOMES_PERMISSOES[permissao]}\n"
        )

        cargos_validos = []

        for cargo_id in cargos:

            cargo = guild.get_role(cargo_id)

            if cargo:
                cargos_validos.append(
                    cargo.mention
                )

        if cargos_validos:
            texto += "\n".join(
                f"• {cargo}"
                for cargo in cargos_validos
            )
        else:
            texto += "• Nenhum cargo configurado."

        texto += "\n"

    return texto


# =========================================================
# PAINEL PRINCIPAL DE PERMISSÕES
# =========================================================

class PainelPermissoesView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(
        label="Adicionar permissão",
        emoji="➕",
        style=discord.ButtonStyle.success,
        custom_id="cb_permissao_adicionar"
    )
    async def adicionar(
        self,
        interaction,
        button
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este painel.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔐 Escolha qual permissão deseja liberar:",
            view=PermissaoView(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Remover permissão",
        emoji="➖",
        style=discord.ButtonStyle.danger,
        custom_id="cb_permissao_remover"
    )
    async def remover(
        self,
        interaction,
        button
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este painel.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🗑️ Escolha qual permissão deseja remover:",
            view=RemoverPermissaoView(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Ver permissões",
        emoji="📋",
        style=discord.ButtonStyle.primary,
        custom_id="cb_permissao_ver"
    )
    async def ver(
        self,
        interaction,
        button
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar este painel.",
                ephemeral=True
            )
            return

        texto = await criar_lista_permissoes(
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
    description="Cria o painel para configurar cargos"
)
async def painelpermissoes(
    interaction: discord.Interaction
):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ Apenas administradores podem criar o painel.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="⚙️ CONFIGURAÇÃO DE PERMISSÕES",
        description=(
            "Use os botões abaixo para configurar "
            "os cargos do servidor.\n\n"
            "➕ **Adicionar permissão**\n"
            "Escolha o cargo e a função que ele poderá usar.\n\n"
            "➖ **Remover permissão**\n"
            "Retire uma função de um cargo.\n\n"
            "📋 **Ver permissões**\n"
            "Veja todos os cargos configurados."
        ),
        color=discord.Color.gold()
    )

    await interaction.channel.send(
        embed=embed,
        view=PainelPermissoesView()
    )

    await interaction.response.send_message(
        "✅ Painel de permissões criado!",
        ephemeral=True
    )


# =========================================================
# /CRIARRANKING
# =========================================================

@tree.command(
    name="criarranking",
    description="Cria o ranking das favelas"
)
async def criarranking(
    interaction: discord.Interaction
):

    if not possui_permissao(
        interaction,
        "criar_ranking"
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

    dados = novo_ranking()

    ranking_message = await interaction.channel.send(
        embed=criar_embed_ranking(dados)
    )

    globals()["ranking_message"] = ranking_message

    await enviar_webhook(
        WEBHOOK_RANKING,
        discord.Embed(
            title="🏆 RANKING CRIADO",
            description=(
                f"👤 Criado por: "
                f"{interaction.user.mention}\n"
                f"📍 Canal: "
                f"{interaction.channel.mention}"
            ),
            color=discord.Color.blue()
        )
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
async def ranking(
    interaction: discord.Interaction
):

    await interaction.response.defer(
        ephemeral=True
    )

    dados = await carregar_ranking()

    if dados is None:

        await interaction.followup.send(
            "❌ Ranking não encontrado. "
            "Use /criarranking.",
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
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    if not possui_permissao(
        interaction,
        "adicionar"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para adicionar gastos.",
            ephemeral=True
        )

        return

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

    dados[favela] += valor

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar o ranking.",
            ephemeral=True
        )

        return

    await enviar_webhook(
        WEBHOOK_ADICIONAR,
        discord.Embed(
            title="➕ GASTO ADICIONADO",
            description=(
                f"👤 **Responsável:** "
                f"{interaction.user.mention}\n"
                f"🏘️ **Favela:** {favela}\n"
                f"💰 **Adicionado:** "
                f"+{dinheiro(valor)}\n"
                f"📊 **Total:** "
                f"{dinheiro(dados[favela])}"
            ),
            color=discord.Color.green()
        )
    )

    await interaction.followup.send(
        f"✅ **{favela}** recebeu "
        f"**{dinheiro(valor)}**.\n"
        f"📊 Total: "
        f"**{dinheiro(dados[favela])}**",
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
    interaction: discord.Interaction,
    favela: str,
    valor: int
):

    if not possui_permissao(
        interaction,
        "remover"
    ):

        await interaction.response.send_message(
            "❌ Você não tem permissão para remover gastos.",
            ephemeral=True
        )

        return

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

    await enviar_webhook(
        WEBHOOK_REMOVER,
        discord.Embed(
            title="➖ GASTO REMOVIDO",
            description=(
                f"👤 **Responsável:** "
                f"{interaction.user.mention}\n"
                f"🏘️ **Favela:** {favela}\n"
                f"💰 **Removido:** "
                f"-{dinheiro(valor)}\n"
                f"📊 **Total:** "
                f"{dinheiro(dados[favela])}"
            ),
            color=discord.Color.red()
        )
    )

    await interaction.followup.send(
        f"✅ Gasto removido de **{favela}**.\n"
        f"📊 Total: "
        f"**{dinheiro(dados[favela])}**",
        ephemeral=True
    )


# =========================================================
# /GASTOTOTAL
# =========================================================

@tree.command(
    name="gastototal",
    description="Mostra o total gasto"
)
@app_commands.describe(
    favela="Nome da favela"
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
        f"💰 Total: "
        f"**{dinheiro(dados[favela])}**",
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

    if not possui_permissao(
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

    dados = novo_ranking()

    sucesso = await atualizar_ranking(dados)

    if not sucesso:

        await interaction.followup.send(
            "❌ Não consegui atualizar.",
            ephemeral=True
        )

        return

    await enviar_webhook(
        WEBHOOK_RANKING,
        discord.Embed(
            title="🗑️ RANKING ZERADO",
            description=(
                f"👤 Responsável: "
                f"{interaction.user.mention}"
            ),
            color=discord.Color.red()
        )
    )

    await interaction.followup.send(
        "✅ Ranking zerado.",
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

    print(
        f"❌ Erro no comando: {error}"
    )

    try:

        mensagem = (
            "❌ Ocorreu um erro ao executar o comando."
        )

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

    except Exception:
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
            f"❌ Erro sincronizando comandos: "
            f"{erro}"
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
            f"❌ Erro procurando ranking: "
            f"{erro}"
        )


# =========================================================
# INICIAR
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
