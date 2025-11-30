import flet as ft
import edge_tts
import asyncio

def main(page: ft.Page):
    # --- 1. Configurações Visuais ---
    page.title = "Studio Narrator Mobile Turbo"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"

    # --- 2. Estrutura de Dados Otimizada (Cache) ---
    dados_cacheados = {} 
    mapa_tecnico_vozes = {} 

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

    # --- 3. Elementos da Interface (AGORA LARGOS) ---
    titulo = ft.Text("🎙️ Studio Turbo", size=28, weight="bold", color="green")
    subtitulo = ft.Text("Iniciando...", color="grey", size=12)

    # A MÁGICA: width=float("inf") faz ocupar a tela toda
    dd_idioma = ft.Dropdown(
        label="Idioma", 
        prefix_icon=ft.Icons.LANGUAGE, 
        disabled=True, 
        width=float("inf")
    )
    dd_regiao = ft.Dropdown(
        label="Região", 
        prefix_icon=ft.Icons.MAP, 
        disabled=True, 
        width=float("inf")
    )
    dd_voz = ft.Dropdown(
        label="Narrador", 
        prefix_icon=ft.Icons.RECORD_VOICE_OVER, 
        disabled=True, 
        width=float("inf")
    )

    # Sliders
    slider_vel = ft.Slider(min=-50, max=50, divisions=20, value=5, label="{value}%")
    lbl_vel = ft.Text("Velocidade: +5%", size=12)
    slider_pitch = ft.Slider(min=-50, max=50, divisions=20, value=-7, label="{value}Hz")
    lbl_pitch = ft.Text("Tom: -7Hz", size=12)

    def atualizar_sliders(e):
        lbl_vel.value = f"Velocidade: {int(slider_vel.value)}%"
        lbl_pitch.value = f"Tom: {int(slider_pitch.value)}Hz"
        lbl_vel.update()
        lbl_pitch.update()

    slider_vel.on_change = atualizar_sliders
    slider_pitch.on_change = atualizar_sliders

    caixa_texto = ft.TextField(
        label="Roteiro", 
        multiline=True, 
        min_lines=3, 
        prefix_icon=ft.Icons.EDIT_NOTE,
        width=float("inf") # Largura total aqui também
    )
    
    btn_gerar = ft.ElevatedButton(
        text="GERAR ÁUDIO", 
        icon=ft.Icons.PLAY_ARROW, 
        height=50, 
        style=ft.ButtonStyle(bgcolor="green", color="white"),
        disabled=True,
        width=float("inf") # Botãozão largo (melhor para dedão no celular)
    )
    
    lbl_status = ft.Text("", color="grey")

    # --- 4. Lógica "AJAX Style" (Mantida) ---

    def mudar_idioma(e):
        idioma_sel = dd_idioma.value
        if not idioma_sel: return

        # Cache instantâneo
        regioes_do_idioma = sorted(list(dados_cacheados[idioma_sel].keys()))
        
        dd_regiao.options = [ft.dropdown.Option(r) for r in regioes_do_idioma]
        dd_regiao.value = None
        dd_regiao.disabled = False
        
        dd_voz.options = []
        dd_voz.value = None
        dd_voz.disabled = True
        
        if idioma_sel == "Español" and "México" in regioes_do_idioma:
            dd_regiao.value = "México"
            mudar_regiao(None)
            
        page.update()

    def mudar_regiao(e):
        idioma_sel = dd_idioma.value
        regiao_sel = dd_regiao.value
        if not idioma_sel or not regiao_sel: return

        vozes_da_regiao = dados_cacheados[idioma_sel][regiao_sel]
        
        dd_voz.options = [ft.dropdown.Option(v_nome) for v_nome, v_tec in vozes_da_regiao]
        dd_voz.disabled = False
        
        dd_voz.value = None
        if vozes_da_regiao:
            dd_voz.value = vozes_da_regiao[0][0]
            for v_nome, v_tec in vozes_da_regiao:
                if "Jorge" in v_nome:
                    dd_voz.value = v_nome
                    break
        
        page.update()

    dd_idioma.on_change = mudar_idioma
    dd_regiao.on_change = mudar_regiao

    # --- 5. Geração ---
    async def gerar(e):
        texto = caixa_texto.value
        nome_voz = dd_voz.value
        
        if not texto or not nome_voz:
            lbl_status.value = "Erro: Preencha tudo!"; lbl_status.color = "red"; page.update(); return

        btn_gerar.disabled = True
        lbl_status.value = "Gerando..."; lbl_status.color = "yellow"; page.update()

        try:
            voice_id = mapa_tecnico_vozes[nome_voz]
            rate = f"{int(slider_vel.value):+d}%"
            pitch = f"{int(slider_pitch.value):+d}Hz"
            
            await edge_tts.Communicate(texto, voice_id, rate=rate, pitch=pitch).save("audio_turbo.mp3")
            lbl_status.value = "Sucesso: audio_turbo.mp3"; lbl_status.color = "green"
        except Exception as err:
            lbl_status.value = f"Erro: {err}"; lbl_status.color = "red"
        
        btn_gerar.disabled = False; page.update()

    btn_gerar.on_click = gerar

    # --- 6. Carregamento Inicial ---
    async def boot():
        subtitulo.value = "Baixando e indexando vozes..."
        page.update()
        
        try:
            voices = await edge_tts.list_voices()
            
            for v in voices:
                try: locale_lang, locale_reg = v['Locale'].split('-', 1)
                except: continue
                
                nome_idioma = traducao_idiomas.get(locale_lang, locale_lang)
                nome_regiao = traducao_regioes.get(locale_reg, locale_reg)
                short_name = v['ShortName'].split('-')[-1].replace('Neural', '')
                display_name = f"{short_name} ({v['Gender']})"
                
                mapa_tecnico_vozes[display_name] = v['ShortName']

                if nome_idioma not in dados_cacheados: dados_cacheados[nome_idioma] = {}
                if nome_regiao not in dados_cacheados[nome_idioma]: dados_cacheados[nome_idioma][nome_regiao] = []
                
                dados_cacheados[nome_idioma][nome_regiao].append((display_name, v['ShortName']))

            idiomas_ordenados = sorted(list(dados_cacheados.keys()))
            dd_idioma.options = [ft.dropdown.Option(i) for i in idiomas_ordenados]
            dd_idioma.disabled = False
            btn_gerar.disabled = False
            
            subtitulo.value = f"{len(voices)} vozes prontas."
            subtitulo.color = "green"

            if "Español" in dados_cacheados:
                dd_idioma.value = "Español"
                mudar_idioma(None)

            page.update()
            
        except Exception as e:
            subtitulo.value = f"Erro fatal: {e}"; subtitulo.color = "red"; page.update()

    page.add(
        titulo, subtitulo,
        ft.Divider(),
        dd_idioma, dd_regiao, dd_voz,
        ft.Divider(),
        lbl_vel, slider_vel,
        lbl_pitch, slider_pitch,
        ft.Divider(),
        caixa_texto,
        ft.Container(height=10),
        btn_gerar,
        ft.Container(height=10),
        lbl_status
    )

    page.run_task(boot)

ft.app(target=main)