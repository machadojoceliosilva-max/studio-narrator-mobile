import flet as ft
import edge_tts
import asyncio
import os

def main(page: ft.Page):
    # --- 1. Configurações Visuais ---
    page.title = "Jorge Narrator V5 (Fixed)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"

    # --- 2. Gerenciador de Permissões ---
    ph = ft.PermissionHandler()
    page.overlay.append(ph)

    # --- 3. Variáveis e Dados ---
    dados_cacheados = {} 
    mapa_tecnico_vozes = {} 
    
    # (Seus dicionários de tradução continuam iguais aqui...)
    traducao_idiomas = {
        "pt": "Português", "en": "English", "es": "Español", "fr": "Français",
        "de": "Deutsch", "it": "Italiano", "ja": "Japonês", "ru": "Russo", "zh": "Chinês"
    }
    traducao_regioes = {
        "BR": "Brasil", "PT": "Portugal", "US": "EUA", "GB": "Reino Unido",
        "ES": "Espanha", "MX": "México", "AR": "Argentina", "CO": "Colômbia",
        "VE": "Venezuela", "PE": "Peru", "CL": "Chile", "EC": "Equador",
        "IN": "Índia"
    }

    # --- 4. Elementos da Interface ---
    titulo = ft.Text("🎙️ Jorge V5", size=28, weight="bold", color="green")
    subtitulo = ft.Text("Iniciando...", color="grey", size=12)

    dd_idioma = ft.Dropdown(label="Idioma", prefix_icon=ft.Icons.LANGUAGE, disabled=True, width=float("inf"))
    dd_regiao = ft.Dropdown(label="Região", prefix_icon=ft.Icons.MAP, disabled=True, width=float("inf"))
    dd_voz = ft.Dropdown(label="Narrador", prefix_icon=ft.Icons.RECORD_VOICE_OVER, disabled=True, width=float("inf"))

    slider_vel = ft.Slider(min=-50, max=50, divisions=20, value=5, label="{value}%")
    lbl_vel = ft.Text("Velocidade: +5%", size=12)
    slider_pitch = ft.Slider(min=-50, max=50, divisions=20, value=-7, label="{value}Hz")
    lbl_pitch = ft.Text("Tom: -7Hz", size=12)

    def atualizar_sliders(e):
        lbl_vel.value = f"Velocidade: {int(slider_vel.value)}%"
        lbl_pitch.value = f"Tom: {int(slider_pitch.value)}Hz"
        lbl_vel.update(); lbl_pitch.update()

    slider_vel.on_change = atualizar_sliders
    slider_pitch.on_change = atualizar_sliders

    caixa_texto = ft.TextField(label="Roteiro", multiline=True, min_lines=3, prefix_icon=ft.Icons.EDIT_NOTE, width=float("inf"))
    
    # Botão Simplificado
    btn_gerar = ft.ElevatedButton(
        text="SALVAR EM DOWNLOADS", 
        icon=ft.Icons.DOWNLOAD, 
        height=50, 
        style=ft.ButtonStyle(bgcolor="green", color="white"),
        disabled=True,
        width=float("inf")
    )
    
    lbl_status = ft.Text("", color="grey")

    # --- 5. Lógica de Menus (Igual ao anterior) ---
    def mudar_idioma(e):
        idioma_sel = dd_idioma.value
        if not idioma_sel: return
        regioes = sorted(list(dados_cacheados[idioma_sel].keys()))
        dd_regiao.options = [ft.dropdown.Option(r) for r in regioes]
        dd_regiao.value = None; dd_regiao.disabled = False
        dd_voz.options = []; dd_voz.value = None; dd_voz.disabled = True
        
        if idioma_sel == "Español" and "México" in regioes:
            dd_regiao.value = "México"
            mudar_regiao(None)
        page.update()

    def mudar_regiao(e):
        idioma_sel = dd_idioma.value
        regiao_sel = dd_regiao.value
        if not idioma_sel or not regiao_sel: return
        vozes = dados_cacheados[idioma_sel][regiao_sel]
        dd_voz.options = [ft.dropdown.Option(v[0]) for v in vozes]
        dd_voz.disabled = False
        dd_voz.value = vozes[0][0] if vozes else None
        for v in vozes:
            if "Jorge" in v[0]: dd_voz.value = v[0]; break
        page.update()

    dd_idioma.on_change = mudar_idioma
    dd_regiao.on_change = mudar_regiao

    # --- 6. O PULO DO GATO: Salvar Direto em Downloads ---
    async def pedir_permissao_e_salvar(e):
        # 1. Tenta pedir permissão de armazenamento
        # Obs: No Android 11+ isso às vezes é ignorado se for pasta pública, 
        # mas no Android 10 é obrigatório.
        ph.request_permission(ft.PermissionType.STORAGE)
        
        # Como o pedido é assíncrono, vamos tentar salvar direto.
        # Se der erro de permissão, o usuário aceita e tenta de novo.
        await gerar_audio_task()

    async def gerar_audio_task():
        texto = caixa_texto.value
        if not texto:
            lbl_status.value = "Digite um roteiro!"; lbl_status.color = "red"; page.update()
            return

        btn_gerar.disabled = True
        lbl_status.value = "Processando..."; lbl_status.color = "yellow"
        page.update()

        try:
            nome_voz = dd_voz.value
            voice_id = mapa_tecnico_vozes[nome_voz]
            rate = f"{int(slider_vel.value):+d}%"
            pitch = f"{int(slider_pitch.value):+d}Hz"
            
            # CAMINHO MÁGICO DO ANDROID
            # /storage/emulated/0/Download/ é a pasta Downloads padrão
            nome_arquivo = "narracao_jorge.mp3"
            caminho_final = f"/storage/emulated/0/Download/{nome_arquivo}"
            
            # Se estiver no PC (Windows), salva na pasta local para não dar erro
            if os.name == 'nt': 
                caminho_final = nome_arquivo

            communicate = edge_tts.Communicate(texto, voice_id, rate=rate, pitch=pitch)
            await communicate.save(caminho_final)

            lbl_status.value = f"Salvo na pasta Downloads!\nArquivo: {nome_arquivo}"
            lbl_status.color = "green"
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Sucesso! Verifique a pasta Downloads."))
            page.snack_bar.open = True

        except Exception as err:
            lbl_status.value = f"Erro: {err}\nVerifique as permissões do App."
            lbl_status.color = "red"
        
        btn_gerar.disabled = False
        page.update()

    btn_gerar.on_click = pedir_permissao_e_salvar

    # --- 7. Boot (Igual) ---
    async def boot():
        subtitulo.value = "Indexando vozes..."
        page.update()
        try:
            voices = await edge_tts.list_voices()
            for v in voices:
                try: l, r = v['Locale'].split('-', 1)
                except: continue
                nome_l = traducao_idiomas.get(l, l)
                nome_r = traducao_regioes.get(r, r)
                short = v['ShortName'].split('-')[-1].replace('Neural', '')
                disp = f"{short} ({v['Gender']})"
                mapa_tecnico_vozes[disp] = v['ShortName']
                if nome_l not in dados_cacheados: dados_cacheados[nome_l] = {}
                if nome_r not in dados_cacheados[nome_l]: dados_cacheados[nome_l][nome_r] = []
                dados_cacheados[nome_l][nome_r].append((disp, v['ShortName']))

            idiomas = sorted(list(dados_cacheados.keys()))
            dd_idioma.options = [ft.dropdown.Option(i) for i in idiomas]
            dd_idioma.disabled = False
            btn_gerar.disabled = False
            subtitulo.value = f"{len(voices)} vozes prontas."
            subtitulo.color = "green"

            if "Español" in dados_cacheados:
                dd_idioma.value = "Español"
                mudar_idioma(None)
            page.update()
        except Exception as e:
            subtitulo.value = f"Erro: {e}"; page.update()

    page.add(
        titulo, subtitulo, ft.Divider(),
        dd_idioma, dd_regiao, dd_voz, ft.Divider(),
        lbl_vel, slider_vel, lbl_pitch, slider_pitch, ft.Divider(),
        caixa_texto, ft.Container(height=10),
        btn_gerar, ft.Container(height=10), lbl_status
    )
    page.run_task(boot)

ft.app(target=main)
