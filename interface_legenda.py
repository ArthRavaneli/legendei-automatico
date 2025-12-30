import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import whisper
import torch
import os
import math
import sys
import re
import ctypes
from deep_translator import GoogleTranslator

# --- FUNÇÃO AUXILIAR PARA ARQUIVOS NO EXE ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto, funcionando tanto para dev quanto para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- FEEDBACK VISUAL ---
class RedirecionadorTexto:
    def __init__(self, widget_var, root):
        self.widget_var = widget_var
        self.root = root

    def write(self, text):
        if text and text.strip():
            self.root.after(0, lambda: self._atualizar_label(text))

    def _atualizar_label(self, text):
        texto_limpo = text.replace("\r", "").replace("\n", "").strip()
        if len(texto_limpo) < 3: return

        match_porcentagem = re.search(r"(\d{1,3})%", texto_limpo)
        
        if match_porcentagem:
            porcentagem = match_porcentagem.group(1)
            self.widget_var.set(f"⏳ Processando... {porcentagem}%")
        elif "Downloading" in texto_limpo or "it/s" in texto_limpo:
             self.widget_var.set(f"📥 Baixando arquivos: {texto_limpo[:30]}...")

    def flush(self):
        pass

# --- CONSTANTES ---
LANGUAGES = {
    "Português": "pt", "Inglês": "en", "Espanhol": "es", "Francês": "fr",
    "Alemão": "de", "Italiano": "it", "Japonês": "ja", "Chinês": "zh", "Russo": "ru"
}

INFO_MODELOS = {
    "tiny": "Rascunho Rápido: Baixa precisão. Instantâneo.",
    "base": "Básico: Bom para áudios limpos.",
    "small": "Recomendado (Padrão): Equilíbrio perfeito.",
    "medium": "Cinema/Séries: Alta precisão (Requer GPU boa).",
    "large": "Máxima Precisão (3GB): O mais pesado e inteligente."
}

EXTENSOES_VIDEO = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.mpeg', '.mp3', '.wav')

CORES = {
    "bg": "#2b2b2b", "fg": "#ffffff", "accent": "#007acc",
    "panel": "#333333", "button": "#404040", "button_hover": "#505050",
    "input_bg": "#ffffff", "input_fg": "#000000", "info_text": "#4fc3f7",
    "status_text": "#ff9800", "danger": "#ff5555"       
}

class LegendadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Legendas Pro IA - Batch Edition")
        self.root.geometry("760x820")
        self.root.configure(bg=CORES["bg"])
        
        # Configuração ID App Windows
        try:
            myappid = 'legendador.ia.whisper.v2' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            icon_path = resource_path("icone.ico")
            self.root.iconbitmap(icon_path)
        except Exception: pass

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configurar_estilos()

        # --- Variáveis de Controle ---
        self.modo_operacao = tk.StringVar(value="arquivo")
        self.caminho_origem = tk.StringVar()
        self.caminho_destino = tk.StringVar()
        
        self.device_var = tk.StringVar(value="GPU (Recomendado)")
        self.model_var = tk.StringVar(value="small")
        self.lang_origem_var = tk.StringVar(value="Inglês")
        self.lang_destino_var = tk.StringVar(value="Português")
        self.info_modelo_txt = tk.StringVar()
        self.status_sistema_var = tk.StringVar(value="Aguardando comando...")
        
        self.stop_event = threading.Event()

        self.criar_interface()
        self.atualizar_info_modelo() 

    def configurar_estilos(self):
        self.style.configure("TFrame", background=CORES["bg"])
        self.style.configure("TLabelframe", background=CORES["bg"], foreground=CORES["fg"])
        self.style.configure("TLabelframe.Label", background=CORES["bg"], foreground=CORES["accent"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabel", background=CORES["bg"], foreground=CORES["fg"], font=("Segoe UI", 10))
        self.style.configure("TRadiobutton", background=CORES["bg"], foreground=CORES["fg"], font=("Segoe UI", 10))
        self.style.map("TRadiobutton", background=[("active", CORES["bg"])])
        
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=CORES["button"], foreground="white", borderwidth=1)
        self.style.map("TButton", background=[("active", CORES["button_hover"])])
        self.style.configure("Accent.TButton", background=CORES["accent"], foreground="white", font=("Segoe UI", 11, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#005f9e")])
        self.style.configure("TEntry", fieldbackground=CORES["input_bg"], foreground=CORES["input_fg"])
        self.style.configure("TCombobox", fieldbackground=CORES["input_bg"], foreground=CORES["input_fg"], background=CORES["button"])
        self.root.option_add("*TCombobox*Listbox*Background", CORES["input_bg"])
        self.root.option_add("*TCombobox*Listbox*Foreground", CORES["input_fg"])

    def criar_interface(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Legendas Automáticas (Whisper)", 
                 bg=CORES["bg"], fg=CORES["accent"], font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

        # --- SEÇÃO 1: SELEÇÃO DE ARQUIVOS ---
        pnl_arquivo = ttk.LabelFrame(main_frame, text=" Passo 1: Seleção de Origem e Destino ", padding="15")
        pnl_arquivo.pack(fill=tk.X, pady=5)
        
        frame_radio = ttk.Frame(pnl_arquivo)
        frame_radio.pack(fill=tk.X, pady=(0, 10))
        ttk.Radiobutton(frame_radio, text="Arquivo Único", variable=self.modo_operacao, value="arquivo", command=self.limpar_paths).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(frame_radio, text="Pasta Completa (Lote)", variable=self.modo_operacao, value="pasta", command=self.limpar_paths).pack(side=tk.LEFT, padx=10)

        # Input Origem
        lbl_origem = ttk.Label(pnl_arquivo, text="Origem (Arquivo ou Pasta):")
        lbl_origem.pack(anchor="w")
        frame_input = ttk.Frame(pnl_arquivo)
        frame_input.pack(fill=tk.X, pady=(0, 10))
        tk.Entry(frame_input, textvariable=self.caminho_origem, bg=CORES["input_bg"], fg=CORES["input_fg"], 
                 font=("Consolas", 10), bd=0, highlightthickness=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        ttk.Button(frame_input, text="📂 Procurar...", command=self.escolher_origem).pack(side=tk.RIGHT)

        # Input Destino
        lbl_dest = ttk.Label(pnl_arquivo, text="Pasta de Destino (Opcional - Deixe vazio para salvar na origem):")
        lbl_dest.pack(anchor="w")
        frame_dest = ttk.Frame(pnl_arquivo)
        frame_dest.pack(fill=tk.X)
        tk.Entry(frame_dest, textvariable=self.caminho_destino, bg=CORES["input_bg"], fg=CORES["input_fg"], 
                 font=("Consolas", 10), bd=0, highlightthickness=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        ttk.Button(frame_dest, text="📂 Selecionar Pasta...", command=self.escolher_destino).pack(side=tk.RIGHT)

        # --- SEÇÃO 2: CONFIGURAÇÕES ---
        pnl_config = ttk.LabelFrame(main_frame, text=" Passo 2: Configurações ", padding="15")
        pnl_config.pack(fill=tk.X, pady=15)
        
        pnl_config.columnconfigure(1, weight=1)
        pnl_config.columnconfigure(3, weight=1)
        
        ttk.Label(pnl_config, text="Processamento:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(pnl_config, textvariable=self.device_var, values=["GPU (Recomendado)", "CPU (Lento)"], state="readonly").grid(row=0, column=1, sticky="ew", padx=(5, 15))
        
        ttk.Label(pnl_config, text="Precisão:").grid(row=0, column=2, sticky="w", pady=5)
        combo_mod = ttk.Combobox(pnl_config, textvariable=self.model_var, values=list(INFO_MODELOS.keys()), state="readonly")
        combo_mod.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        combo_mod.bind("<<ComboboxSelected>>", self.atualizar_info_modelo)

        ttk.Label(pnl_config, text="Idioma Vídeo:").grid(row=1, column=0, sticky="w", pady=15)
        ttk.Combobox(pnl_config, textvariable=self.lang_origem_var, values=list(LANGUAGES.keys()), state="readonly").grid(row=1, column=1, sticky="ew", padx=(5, 15))
        
        ttk.Label(pnl_config, text="Traduzir para:").grid(row=1, column=2, sticky="w", pady=15)
        ttk.Combobox(pnl_config, textvariable=self.lang_destino_var, values=list(LANGUAGES.keys()), state="readonly").grid(row=1, column=3, sticky="ew", padx=(5, 0))

        frame_info = tk.Frame(pnl_config, bg=CORES["panel"], bd=1, relief="flat")
        frame_info.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(15, 0))
        tk.Label(frame_info, textvariable=self.info_modelo_txt, bg=CORES["panel"], fg=CORES["info_text"], 
                 font=("Segoe UI", 9), justify="center", pady=8).pack(fill=tk.BOTH)

        # --- BOTÕES E STATUS ---
        self.btn_run = ttk.Button(main_frame, text="🚀 INICIAR PROCESSO", style="Accent.TButton", command=self.iniciar_thread)
        self.btn_run.pack(fill=tk.X, pady=(10, 0), ipady=5)

        lbl_status = tk.Label(main_frame, textvariable=self.status_sistema_var, bg=CORES["bg"], fg=CORES["status_text"], font=("Consolas", 9, "bold"))
        lbl_status.pack(pady=(5, 0))

        self.btn_cancelar = tk.Button(main_frame, text="cancelar operação", command=self.cancelar_operacao, font=("Segoe UI", 8),
                                      bg=CORES["bg"], fg=CORES["danger"], activebackground=CORES["bg"], activeforeground="#ff0000",
                                      relief="flat", bd=0, cursor="hand2", state="disabled")
        self.btn_cancelar.pack(pady=(0, 10))

        tk.Label(main_frame, text="Log Detalhado:", bg=CORES["bg"], fg="white").pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=8, bg="black", fg="#00ff00", font=("Consolas", 9), state='disabled', bd=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    # --- LÓGICA DE INTERFACE ---
    def limpar_paths(self):
        self.caminho_origem.set("")

    def atualizar_info_modelo(self, event=None):
        modelo = self.model_var.get()
        self.info_modelo_txt.set(f'ℹ {INFO_MODELOS.get(modelo, "")}')

    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, ">> " + mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def escolher_origem(self):
        if self.modo_operacao.get() == "arquivo":
            path = filedialog.askopenfilename(filetypes=[("Vídeos", "*" + " *".join(EXTENSOES_VIDEO)), ("Todos", "*.*")])
        else:
            path = filedialog.askdirectory()
        if path: self.caminho_origem.set(path)

    def escolher_destino(self):
        path = filedialog.askdirectory()
        if path: self.caminho_destino.set(path)

    def cancelar_operacao(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.status_sistema_var.set("Solicitando cancelamento...")
            self.log("!!! CANCELAMENTO SOLICITADO !!!")
            self.btn_cancelar.config(state="disabled", text="Parando...")

    def resetar_interface(self):
        self.btn_run.config(state="normal", text="🚀 INICIAR PROCESSO")
        self.btn_cancelar.config(state="disabled", text="cancelar operação")
        sys.stderr = sys.__stderr__

    def format_timestamp(self, seconds):
        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        milliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    # --- MOTOR DA IA E LÓGICA DE LOTE ---
    def iniciar_thread(self):
        origem = self.caminho_origem.get()
        if not origem:
            messagebox.showwarning("Atenção", "Selecione a Origem primeiro!")
            return
        
        # Prepara lista de arquivos
        lista_arquivos = []
        if self.modo_operacao.get() == "arquivo":
            if os.path.isfile(origem):
                lista_arquivos.append(origem)
        else:
            if os.path.isdir(origem):
                for root, dirs, files in os.walk(origem):
                    for file in files:
                        if file.lower().endswith(EXTENSOES_VIDEO):
                            lista_arquivos.append(os.path.join(root, file))
        
        if not lista_arquivos:
            messagebox.showerror("Erro", "Nenhum arquivo de vídeo encontrado!")
            return

        self.stop_event.clear()
        self.btn_run.config(state="disabled", text="Processando...")
        self.btn_cancelar.config(state="normal", text="cancelar operação")
        
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        threading.Thread(target=self.executar_processamento_em_lote, args=(lista_arquivos,), daemon=True).start()

    # --- CORREÇÃO: Função indentada corretamente dentro da classe ---
    def executar_processamento_em_lote(self, lista_arquivos):
        stderr_original = sys.stderr
        
        try:
            sys.stderr = RedirecionadorTexto(self.status_sistema_var, self.root)
            
            # Carregar Configurações
            model_name = self.model_var.get()
            device_choice = self.device_var.get()
            use_gpu = "GPU" in device_choice
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            self.log(f"Hardware Selecionado: {device.upper()}")
            self.log(f"Carregando Modelo {model_name} (Aguarde)...")
            self.status_sistema_var.set("Carregando Modelo IA...")
            
            # Carrega modelo uma única vez
            model = whisper.load_model(model_name, device=device)
            self.log("Modelo Carregado! Iniciando fila...")
            
            total = len(lista_arquivos)
            pasta_destino_fixa = self.caminho_destino.get()
            
            # Listas para relatório final
            sucessos = 0
            erros = []

            # --- LOOP PRINCIPAL DOS ARQUIVOS ---
            for index, video_path in enumerate(lista_arquivos):
                if self.stop_event.is_set(): break
                
                nome_arq = os.path.basename(video_path)
                self.status_sistema_var.set(f"Processando {index+1}/{total}: {nome_arq}")
                
                # --- TRY/EXCEPT DENTRO DO LOOP ---
                try:
                    self.log(f"--- Início ({index+1}/{total}): {nome_arq} ---")
                    
                    if pasta_destino_fixa and os.path.isdir(pasta_destino_fixa):
                        pasta_final = pasta_destino_fixa
                    else:
                        pasta_final = os.path.dirname(video_path)
                    
                    nome_sem_ext = os.path.splitext(nome_arq)[0]
                    caminho_srt = os.path.join(pasta_final, f"{nome_sem_ext}.srt")

                    self.transcrever_video(model, video_path, caminho_srt, stderr_original)
                    
                    self.log(f"✅ Salvo em: {caminho_srt}")
                    sucessos += 1

                except Exception as e_arquivo:
                    msg_erro = str(e_arquivo)
                    self.log(f"❌ ERRO no arquivo '{nome_arq}':")
                    self.log(f"   -> {msg_erro}")
                    erros.append(f"{nome_arq} ({msg_erro})")
                
                self.log("---------------------------")

            # --- FINALIZAÇÃO E RELATÓRIO ---
            if self.stop_event.is_set():
                self.status_sistema_var.set("Processo Interrompido.")
                messagebox.showwarning("Cancelado", "A fila foi interrompida pelo usuário.")
            else:
                self.status_sistema_var.set("Fila finalizada!")
                resumo = f"Processamento Concluído!\n\n✅ Sucessos: {sucessos}\n❌ Falhas: {len(erros)}"
                if erros:
                    resumo += "\n\nArquivos com erro:\n" + "\n".join(erros[:5])
                    if len(erros) > 5: resumo += "\n... e outros."
                
                self.log("--- RESUMO FINAL ---")
                self.log(f"Sucessos: {sucessos} | Falhas: {len(erros)}")
                
                if erros:
                    messagebox.showwarning("Concluído com Erros", resumo)
                else:
                    messagebox.showinfo("Sucesso Total", resumo)

        except Exception as e:
            self.status_sistema_var.set("Erro Fatal")
            self.log(f"ERRO CRÍTICO NO SISTEMA: {str(e)}")
            messagebox.showerror("Erro Crítico", str(e))
        finally:
            sys.stderr = stderr_original
            self.root.after(0, self.resetar_interface)

    # --- CORREÇÃO: Função indentada corretamente dentro da classe ---
    def transcrever_video(self, model, video_path, output_srt, stderr_original):
        lang_origem = LANGUAGES[self.lang_origem_var.get()]
        lang_dest = LANGUAGES[self.lang_destino_var.get()]
        
        result = model.transcribe(video_path, fp16=False, language=lang_origem, verbose=False)
        
        precisa_traduzir = (lang_origem != lang_dest)
        tradutor = None
        if precisa_traduzir:
            self.log(f"Traduzindo para {self.lang_destino_var.get()}...")
            tradutor = GoogleTranslator(source=lang_origem, target=lang_dest)

        with open(output_srt, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result['segments']):
                if self.stop_event.is_set(): return 
                
                start = self.format_timestamp(segment['start'])
                end = self.format_timestamp(segment['end'])
                text = segment['text'].strip()
                
                if precisa_traduzir and tradutor:
                    try:
                        text = tradutor.translate(text)
                    except: pass
                
                f.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)
    
    if sys.stderr is None: 
        class NullWriter:
            def write(self, s): pass
            def flush(self): pass
        sys.stderr = NullWriter()

    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()