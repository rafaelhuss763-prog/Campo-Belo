import os
import base64
import json
import discord
from discord import app_commands

# =========================================================
# CONFIGURAÇÃO
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# COLE OS WEBHOOKS DIRETAMENTE NO TEMALIX
WEBHOOK_ADICIONAR = "https://discord.com/api/webhooks/1546272715818672218/M2uvS74jTofIkxj_mkR70p-YaiTgYpmUHnYNnDe70NcrJCRoOlGDdinlQRDf7z_5Vt6T"
WEBHOOK_REMOVER = "https://discord.com/api/webhooks/1546273099987554389/j3yWVi6gLdx8saZKuoQ4L2MHe8BcoBaIHgzeQWSRALVfpBrcuYdX9YXR6uXWFi7ptoDd"
WEBHOOK_RANKING = "https://discord.com/api/webhooks/1546273377541423124/8M1YJqPtCkcZ-Z9RGfCMrRk0_7xFpufUBUoW5PH-KLGfDbLPstm-c7s8co3LKIUwD1gF"
WEBHOOK_ENCOMENDAS = "https://discord.com/api/webhooks/1546309841700528218/PnoBJc75hdTK9Oz6VlizYxGgulmSOpyjT_OIlNREqBuPuCF8Y0RYakYRTZLN_Ho4s-9r"


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
# PRODUTOS PERMITIDOS
# =========================================================

PRODUTOS = {
    "Reparo básico": 10000,
    "Colete de proteção": 3000,
    "Lockpick de cobre": 9000,
    "Micha": 6000,
    "Jammer": 3000
}


# =========================================================
# BOT
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

ranking_message = None

# Carrinhos temporários
carrinhos = {}


# =========================================================
# UTILIDADES
# =========================================================

def dinheiro(valor):
    return f"R$ {valor:,}".replace(",", ".")


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

                resultado[favela] = int(
                    dados[favela]
                )

        return resultado

    except Exception as erro:

        print(
            f"Erro decodificando ranking: {erro}"
        )

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

    dados_codificados = codificar_dados(
        dados
    )

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

    return decodificar_dados(
        codificado
    )


async def procurar_ranking():

    global ranking_message

    if ranking_message:

        try:

            mensagem = await (
                ranking_message.channel
                .fetch_message(
                    ranking_message.id
                )
            )

            dados = ler_dados_ranking(
                mensagem
            )

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

                    if (
                        embed.title
                        != "🏆 RANKING CAMPO BELO"
                    ):
                        continue

                    dados = ler_dados_ranking(
                        message
                    )

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

    return ler_dados_ranking(
        mensagem
    )


async def atualizar_ranking(dados):

    global ranking_message

    if ranking_message is None:

        ranking_message = (
            await procurar_ranking()
        )

    if ranking_message is None:
        return False

    try:

        await ranking_message.edit(
            embed=criar_embed_ranking(
                dados
            )
        )

        return True

    except Exception as erro:

        print(
            f"Erro atualizando ranking: {erro}"
        )

        ranking_message = None

        return False


# =========================================================
# WEBHOOKS
# =========================================================

async def enviar_webhook(
    url,
    embed
):

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
# CARRINHO
# =========================================================

def calcular_total(carrinho):

    total = 0

    for produto, quantidade in carrinho.items():

        preco = PRODUTOS.get(
            produto,
            0
        )

        total += preco * quantidade

    return total


def texto_carrinho(carrinho):

    if not carrinho:

        return "🛒 **Carrinho vazio.**"

    linhas = []

    for produto, quantidade in carrinho.items():

        preco = PRODUTOS[produto]

        subtotal = (
            preco * quantidade
        )

        linhas.append(
            f"• **{produto}** × `{quantidade}` "
            f"= **{dinheiro(subtotal)}**"
        )

    total = calcular_total(
        carrinho
    )

    return (
        "\n".join(linhas)
        + "\n\n"
        + f"💰 **TOTAL: {dinheiro(total)}**"
    )


# =========================================================
# MODAL DE QUANTIDADE
# =========================================================

class QuantidadeModal(
    discord.ui.Modal
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Digite somente a quantidade",
        min_length=1,
        max_length=6
    )

    def __init__(
        self,
        produto
    ):

        super().__init__(
            title=f"Quantidade - {produto}"
        )

        self.produto = produto

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite somente números.",
                ephemeral=True
            )

            return

        if quantidade <= 0:

            await interaction.response.send_message(
                "❌ A quantidade precisa ser maior que 0.",
                ephemeral=True
            )

            return

        usuario_id = interaction.user.id

        if usuario_id not in carrinhos:

            carrinhos[usuario_id] = {}

        carrinhos[
            usuario_id
        ][self.produto] = (
            carrinhos[usuario_id].get(
                self.produto,
                0
            ) + quantidade
        )

        await interaction.response.send_message(
            "✅ Item adicionado ao carrinho.\n\n"
            + texto_carrinho(
                carrinhos[usuario_id]
            ),
            ephemeral=True
        )


# =========================================================
# SELECT DE PRODUTO
# =========================================================

class ProdutoSelect(
    discord.ui.Select
):

    def __init__(self):

        opcoes = []

        for nome, preco in PRODUTOS.items():

            opcoes.append(
                discord.SelectOption(
                    label=nome,
                    description=(
                        f"Valor: "
                        f"{dinheiro(preco)}"
                    ),
                    value=nome
                )
            )

        super().__init__(
            placeholder="📦 Escolha um item",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(
        self,
        interaction
    ):

        produto = self.values[0]

        await interaction.response.send_modal(
            QuantidadeModal(produto)
        )


class ProdutoView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=120
        )

        self.add_item(
            ProdutoSelect()
        )


# =========================================================
# ALTERAR QUANTIDADE
# =========================================================

class AlterarModal(
    discord.ui.Modal
):

    quantidade = discord.ui.TextInput(
        label="Nova quantidade",
        placeholder="Digite a nova quantidade",
        min_length=1,
        max_length=6
    )

    def __init__(
        self,
        produto
    ):

        super().__init__(
            title=f"Alterar - {produto}"
        )

        self.produto = produto

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite somente números.",
                ephemeral=True
            )

            return

        if quantidade <= 0:

            await interaction.response.send_message(
                "❌ A quantidade precisa ser maior que 0.",
                ephemeral=True
            )

            return

        usuario_id = interaction.user.id

        if usuario_id not in carrinhos:

            carrinhos[usuario_id] = {}

        carrinhos[
            usuario_id
        ][self.produto] = quantidade

        await interaction.response.send_message(
            "✅ Quantidade alterada.\n\n"
            + texto_carrinho(
                carrinhos[usuario_id]
            ),
            ephemeral=True
        )


class AlterarSelect(
    discord.ui.Select
):

    def __init__(
        self,
        carrinho
    ):

        opcoes = []

        for produto, quantidade in carrinho.items():

            opcoes.append(
                discord.SelectOption(
                    label=produto[:100],
                    description=(
                        f"Atual: {quantidade}"
                    ),
                    value=produto
                )
            )

        super().__init__(
            placeholder="✏️ Escolha o item",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(
        self,
        interaction
    ):

        produto = self.values[0]

        await interaction.response.send_modal(
            AlterarModal(produto)
        )


class AlterarView(
    discord.ui.View
):

    def __init__(
        self,
        carrinho
    ):

        super().__init__(
            timeout=120
        )

        self.add_item(
            AlterarSelect(carrinho)
        )


# =========================================================
# REMOVER ITEM
# =========================================================

class RemoverSelect(
    discord.ui.Select
):

    def __init__(
        self,
        carrinho
    ):

        opcoes = []

        for produto, quantidade in carrinho.items():

            opcoes.append(
                discord.SelectOption(
                    label=produto[:100],
                    description=(
                        f"Quantidade: {quantidade}"
                    ),
                    value=produto
                )
            )

        super().__init__(
            placeholder="🗑️ Escolha o item",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(
        self,
        interaction
    ):

        produto = self.values[0]

        usuario_id = interaction.user.id

        if usuario_id in carrinhos:

            carrinhos[
                usuario_id
            ].pop(
                produto,
                None
            )

        await interaction.response.send_message(
            "🗑️ Item removido.\n\n"
            + texto_carrinho(
                carrinhos.get(
                    usuario_id,
                    {}
                )
            ),
            ephemeral=True
        )


class RemoverView(
    discord.ui.View
):

    def __init__(
        self,
        carrinho
    ):

        super().__init__(
            timeout=120
        )

        self.add_item(
            RemoverSelect(carrinho)
        )


# =========================================================
# VIEW DO TICKET
# =========================================================

class EncomendaView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Adicionar item",
        emoji="➕",
        style=discord.ButtonStyle.success,
        custom_id="cb_adicionar_item"
    )
    async def adicionar(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(
            "📦 Escolha o item:",
            view=ProdutoView(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Alterar quantidade",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        custom_id="cb_alterar_quantidade"
    )
    async def alterar(
        self,
        interaction,
        button
    ):

        carrinho = carrinhos.get(
            interaction.user.id,
            {}
        )

        if not carrinho:

            await interaction.response.send_message(
                "❌ Seu carrinho está vazio.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✏️ Escolha o item:",
            view=AlterarView(carrinho),
            ephemeral=True
        )

    @discord.ui.button(
        label="Remover item",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="cb_remover_item"
    )
    async def remover(
        self,
        interaction,
        button
    ):

        carrinho = carrinhos.get(
            interaction.user.id,
            {}
        )

        if not carrinho:

            await interaction.response.send_message(
                "❌ Seu carrinho está vazio.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🗑️ Escolha o item:",
            view=RemoverView(carrinho),
            ephemeral=True
        )

    @discord.ui.button(
        label="Ver encomenda",
        emoji="📋",
        style=discord.ButtonStyle.secondary,
        custom_id="cb_ver_encomenda"
    )
    async def ver(
        self,
        interaction,
        button
    ):

        carrinho = carrinhos.get(
            interaction.user.id,
            {}
        )

        await interaction.response.send_message(
            texto_carrinho(carrinho),
            ephemeral=True
        )

    @discord.ui.button(
        label="Finalizar",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="cb_finalizar_encomenda"
    )
    async def finalizar(
        self,
        interaction,
        button
    ):

        usuario_id = interaction.user.id

        carrinho = carrinhos.get(
            usuario_id,
            {}
        )

        if not carrinho:

            await interaction.response.send_message(
                "❌ O carrinho está vazio.",
                ephemeral=True
            )

            return

        total = calcular_total(
            carrinho
        )

        resumo = texto_carrinho(
            carrinho
        )

        embed = discord.Embed(
            title="📦 NOVA ENCOMENDA",
            description=(
                f"👤 **Cliente:** "
                f"{interaction.user.mention}\n\n"
                f"{resumo}"
            ),
            color=discord.Color.green()
        )

        embed.set_footer(
            text=f"ID do cliente: {usuario_id}"
        )

        await enviar_webhook(
            WEBHOOK_ENCOMENDAS,
            embed
        )

        carrinhos.pop(
            usuario_id,
            None
        )

        await interaction.response.send_message(
            "✅ **Encomenda finalizada!**\n\n"
            f"{resumo}\n\n"
            "📨 A equipe recebeu o registro.",
            ephemeral=False
        )

    @discord.ui.button(
        label="Cancelar",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="cb_cancelar_encomenda"
    )
    async def cancelar(
        self,
        interaction,
        button
    ):

        carrinhos.pop(
            interaction.user.id,
            None
        )

        await interaction.response.send_message(
            "❌ Encomenda cancelada.",
            ephemeral=True
        )


# =========================================================
# PAINEL PRINCIPAL
# =========================================================

class PainelEncomendaView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Fazer Encomenda",
        emoji="📦",
        style=discord.ButtonStyle.success,
        custom_id="cb_fazer_encomenda"
    )
    async def fazer(
        self,
        interaction,
        button
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ Use isso dentro de um servidor.",
                ephemeral=True
            )

            return

        categoria = discord.utils.get(
            guild.categories,
            name="📦 ENCOMENDAS"
        )

        if categoria is None:

            categoria = await guild.create_category(
                "📦 ENCOMENDAS"
            )

        # Verifica se já existe ticket
        for canal in categoria.text_channels:

            if canal.topic == (
                f"encomenda:{interaction.user.id}"
            ):

                await interaction.response.send_message(
                    f"❌ Você já possui uma encomenda aberta: "
                    f"{canal.mention}",
                    ephemeral=True
                )

                return

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),

            guild.me:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
        }

        nome = (
            "encomenda-"
            + interaction.user.name.lower()
        )

        canal = await guild.create_text_channel(
            nome[:90],
            category=categoria,
            overwrites=overwrites,
            topic=(
                f"encomenda:{interaction.user.id}"
            )
        )

        carrinhos[
            interaction.user.id
        ] = {}

        embed = discord.Embed(
            title="📦 ENCOMENDA",
            description=(
                "Bem-vindo!\n\n"
                "Use **Adicionar item** para começar.\n\n"
                "Você poderá:\n"
                "➕ Adicionar\n"
                "✏️ Alterar quantidade\n"
                "🗑️ Remover\n"
                "📋 Conferir\n"
                "💰 Ver o total\n"
                "✅ Finalizar\n"
                "❌ Cancelar"
            ),
            color=discord.Color.blue()
        )

        await canal.send(
            content=interaction.user.mention,
            embed=embed,
            view=EncomendaView()
        )

        await interaction.response.send_message(
            f"✅ Encomenda criada: {canal.mention}",
            ephemeral=True
        )


# =========================================================
# /CRIARPAINEL
# =========================================================

@tree.command(
    name="criarpainel",
    description="Cria o painel de encomendas"
)
async def criarpainel(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📦 CENTRAL DE ENCOMENDAS",
        description=(
            "Clique em **Fazer Encomenda**.\n\n"
            "Você poderá adicionar itens, "
            "alterar quantidades, remover itens "
            "e conferir o total antes de finalizar."
        ),
        color=discord.Color.blue()
    )

    await interaction.channel.send(
        embed=embed,
        view=PainelEncomendaView()
    )

    await interaction.response.send_message(
        "✅ Painel criado!",
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

    global ranking_message

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

    ranking_message = (
        await interaction.channel.send(
            embed=criar_embed_ranking(
                dados
            )
        )
    )

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
    interaction,
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

    dados[favela] += valor

    sucesso = await atualizar_ranking(
        dados
    )

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
                f"👤 {interaction.user.mention}\n"
                f"🏘️ {favela}\n"
                f"💰 +{dinheiro(valor)}\n"
                f"📊 Total: "
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
    interaction,
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
            f"❌ **{favela}** possui apenas "
            f"**{dinheiro(dados[favela])}**.",
            ephemeral=True
        )

        return

    dados[favela] -= valor

    sucesso = await atualizar_ranking(
        dados
    )

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
                f"👤 {interaction.user.mention}\n"
                f"🏘️ {favela}\n"
                f"💰 -{dinheiro(valor)}\n"
                f"📊 Total: "
                f"{dinheiro(dados[favela])}"
            ),
            color=discord.Color.red()
        )
    )

    await interaction.followup.send(
        "✅ Gasto removido.",
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
    interaction,
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
    interaction
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

    sucesso = await atualizar_ranking(
        dados
    )

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
