import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import whisper
import torch
import os
import math
import sys
from deep_translator import GoogleTranslator

# --- CORREÇÃO DO BUG + FEEDBACK VISUAL ---
class RedirecionadorTexto:
    """
    Captura o texto que iria para o console (stderr) e joga para
    uma variável do Tkinter para o usuário ver o progresso do download.
    """
    def __init__(self, widget_var, root):
        self.widget_var = widget_var
        self.root = root
        self.buffer = ""

    def write(self, text):
        # Filtra apenas textos relevantes ou de progresso
        if text and text.strip():
            # Usa o .after para garantir que a interface não trave ao tentar atualizar de outra thread
            self.root.after(0, lambda: self._atualizar_label(text))

    def _atualizar_label(self, text):
        # Limpa quebras de linha para ficar bonito no Label
        texto_limpo = text.replace("\r", "").replace("\n", "").strip()
        if len(texto_limpo) > 5: # Ignora lixo muito curto
            # Se for barra de progresso do tqdm (ex: 15%|███|), mostramos
            if "%" in texto_limpo or "it/s" in texto_limpo or "Downloading" in texto_limpo:
                self.widget_var.set(f"⏳ STATUS DO SISTEMA: {texto_limpo}")

    def flush(self):
        pass

# --- Mapeamento de Linguagens ---
LANGUAGES = {
    "Português": "pt", "Inglês": "en", "Espanhol": "es", "Francês": "fr",
    "Alemão": "de", "Italiano": "it", "Japonês": "ja", "Chinês": "zh", "Russo": "ru"
}

# --- Guia dos Modelos ---
INFO_MODELOS = {
    "tiny": "Rascunho Rápido: Baixa precisão. Instantâneo. Bom apenas para testar.",
    "base": "Básico: Bom para áudios de estúdio muito limpos. Pode errar pontuação.",
    "small": "Recomendado (Padrão): Equilíbrio perfeito. Ideal para YouTube/Aulas.",
    "medium": "Cinema/Séries: Alta precisão. Entende sotaques e música. (Ideal para RTX 3060).",
    "large": "Máxima Precisão (3GB): O mais inteligente. Se for a 1ª vez, vai demorar para baixar."
}

# --- Cores do Tema (Dark Mode) ---
CORES = {
    "bg": "#2b2b2b", "fg": "#ffffff", "accent": "#007acc",
    "panel": "#333333", "button": "#404040", "button_hover": "#505050",
    "input_bg": "#ffffff", "input_fg": "#000000", "info_text": "#4fc3f7",
    "status_text": "#ff9800" # Laranja para destaque de download
}

class LegendadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Legendas Pro IA")
        self.root.geometry("720x720") # Aumentei um pouco para caber o status
        self.root.configure(bg=CORES["bg"])
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configurar_estilos()

        # Variáveis
        self.video_path = tk.StringVar()
        self.device_var = tk.StringVar(value="GPU (Recomendado)")
        self.model_var = tk.StringVar(value="small")
        self.lang_origem_var = tk.StringVar(value="Inglês")
        self.lang_destino_var = tk.StringVar(value="Português")
        self.info_modelo_txt = tk.StringVar()
        
        # NOVA VARIÁVEL: Para mostrar o status do download em tempo real
        self.status_sistema_var = tk.StringVar(value="Aguardando comando...")

        self.criar_interface()
        self.atualizar_info_modelo() 

    def configurar_estilos(self):
        self.style.configure("TFrame", background=CORES["bg"])
        self.style.configure("TLabelframe", background=CORES["bg"], foreground=CORES["fg"])
        self.style.configure("TLabelframe.Label", background=CORES["bg"], foreground=CORES["accent"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabel", background=CORES["bg"], foreground=CORES["fg"], font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=CORES["button"], foreground="white", borderwidth=1)
        self.style.map("TButton", background=[("active", CORES["button_hover"])])
        self.style.configure("Accent.TButton", background=CORES["accent"], foreground="white", font=("Segoe UI", 11, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#005f9e")])
        self.style.configure("TEntry", fieldbackground=CORES["input_bg"], foreground=CORES["input_fg"])
        self.style.configure("TCombobox", fieldbackground=CORES["input_bg"], foreground=CORES["input_fg"], 
                             background=CORES["button"], arrowcolor="white")
        self.root.option_add("*TCombobox*Listbox*Background", CORES["input_bg"])
        self.root.option_add("*TCombobox*Listbox*Foreground", CORES["input_fg"])

    def criar_interface(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho
        tk.Label(main_frame, text="Legendas Automáticas (Whisper)", 
                 bg=CORES["bg"], fg=CORES["accent"], font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

        # 2. Arquivo
        pnl_arquivo = ttk.LabelFrame(main_frame, text=" Passo 1: Selecione o Vídeo ", padding="15")
        pnl_arquivo.pack(fill=tk.X, pady=5)
        frame_input = ttk.Frame(pnl_arquivo)
        frame_input.pack(fill=tk.X)
        tk.Entry(frame_input, textvariable=self.video_path, bg=CORES["input_bg"], fg=CORES["input_fg"], 
                 font=("Consolas", 10), bd=0, highlightthickness=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        ttk.Button(frame_input, text="📂 Procurar...", command=self.escolher_arquivo).pack(side=tk.RIGHT)

        # 3. Configurações
        pnl_config = ttk.LabelFrame(main_frame, text=" Passo 2: Configurações ", padding="15")
        pnl_config.pack(fill=tk.X, pady=15)
        
        # Grid
        ttk.Label(pnl_config, text="Processamento:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(pnl_config, textvariable=self.device_var, values=["GPU (Recomendado)", "CPU (Lento)"], 
                     state="readonly", width=18).grid(row=0, column=1, sticky="w", padx=10)
        
        ttk.Label(pnl_config, text="Precisão (Modelo):").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        combo_mod = ttk.Combobox(pnl_config, textvariable=self.model_var, values=list(INFO_MODELOS.keys()), 
                                 state="readonly", width=15)
        combo_mod.grid(row=0, column=3, sticky="w", padx=10)
        combo_mod.bind("<<ComboboxSelected>>", self.atualizar_info_modelo)

        ttk.Label(pnl_config, text="Idioma do Vídeo:").grid(row=1, column=0, sticky="w", pady=15)
        ttk.Combobox(pnl_config, textvariable=self.lang_origem_var, values=list(LANGUAGES.keys()), 
                     state="readonly", width=18).grid(row=1, column=1, sticky="w", padx=10)
        
        ttk.Label(pnl_config, text="Traduzir para:").grid(row=1, column=2, sticky="w", pady=15, padx=(20, 0))
        ttk.Combobox(pnl_config, textvariable=self.lang_destino_var, values=list(LANGUAGES.keys()), 
                     state="readonly", width=18).grid(row=1, column=3, sticky="w", padx=10)

        # Info Label
        frame_info = tk.Frame(pnl_config, bg=CORES["panel"], bd=1, relief="flat")
        frame_info.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(15, 0))
        tk.Label(frame_info, textvariable=self.info_modelo_txt, bg=CORES["panel"], fg=CORES["info_text"], 
                 font=("Segoe UI", 9), wraplength=660, justify="left", pady=8, padx=10).pack(fill=tk.BOTH)

        # 4. Botão e STATUS
        self.btn_run = ttk.Button(main_frame, text="🚀 INICIAR PROCESSO", style="Accent.TButton", command=self.iniciar_thread)
        self.btn_run.pack(fill=tk.X, pady=(10, 5), ipady=5)
        
        # --- NOVO: Label de Status do Sistema (Download) ---
        lbl_status = tk.Label(main_frame, textvariable=self.status_sistema_var, 
                              bg=CORES["bg"], fg=CORES["status_text"], font=("Consolas", 9, "bold"))
        lbl_status.pack(pady=(0, 10))

        # 5. Log
        tk.Label(main_frame, text="Log Detalhado:", bg=CORES["bg"], fg="white").pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=8, bg="black", fg="#00ff00", 
                                                  font=("Consolas", 9), state='disabled', bd=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def atualizar_info_modelo(self, event=None):
        modelo = self.model_var.get()
        descricao = INFO_MODELOS.get(modelo, "")
        self.info_modelo_txt.set(f"ℹ️ SOBRE O MODELO '{modelo.upper()}':\n{descricao}")

    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, ">> " + mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def escolher_arquivo(self):
        filename = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.mkv *.avi *.mov *.webm"), ("Todos", "*.*")])
        if filename: self.video_path.set(filename)

    def iniciar_thread(self):
        if not self.video_path.get():
            messagebox.showwarning("Atenção", "Selecione um vídeo primeiro!")
            return
        
        self.btn_run.config(state="disabled", text="Processando... (Aguarde)")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.status_sistema_var.set("Iniciando motor da IA...")
        
        threading.Thread(target=self.processar_video, daemon=True).start()

    def format_timestamp(self, seconds):
        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        milliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def processar_video(self):
        # Salva o stderr original para restaurar depois
        stderr_original = sys.stderr 
        
        try:
            # --- ATIVA O REDIRECIONADOR DE DOWNLOAD ---
            # Agora tudo que o Whisper tentar baixar vai aparecer na tela!
            sys.stderr = RedirecionadorTexto(self.status_sistema_var, self.root)
            
            video_file = self.video_path.get()
            model_name = self.model_var.get()
            device_choice = self.device_var.get()
            lang_origem_nome = self.lang_origem_var.get()
            lang_destino_nome = self.lang_destino_var.get()
            
            use_gpu = "GPU" in device_choice
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            self.log(f"Arquivo: {os.path.basename(video_file)}")
            self.log(f"Hardware: {device.upper()}")
            
            if model_name == "large":
                self.log("⚠️ Verificando arquivos do modelo 'large' (3GB)...")
                self.status_sistema_var.set("Verificando/Baixando modelo IA...")

            self.log(f"Carregando Modelo {model_name}...")
            
            # AQUI ACONTECE O DOWNLOAD
            # O texto de progresso vai aparecer no Label Laranja na tela
            model = whisper.load_model(model_name, device=device)
            
            # Restaura o console normal depois de carregar
            sys.stderr = stderr_original
            self.status_sistema_var.set("IA Carregada! Transcrevendo...")
            
            lang_code_src = LANGUAGES[lang_origem_nome]
            self.log(f"Ouvindo áudio em {lang_origem_nome}...")
            result = model.transcribe(video_file, fp16=False, language=lang_code_src)
            
            lang_code_target = LANGUAGES[lang_destino_nome]
            filename = os.path.splitext(video_file)[0]
            output_srt = f"{filename}_{lang_code_target.upper()}.srt"
            
            precisa_traduzir = (lang_code_src != lang_code_target)
            tradutor = None
            if precisa_traduzir:
                self.status_sistema_var.set("Traduzindo legendas...")
                self.log(f"Traduzindo para {lang_destino_nome}...")
                tradutor = GoogleTranslator(source=lang_code_src, target=lang_code_target)

            self.log("Salvando arquivo .srt...")
            with open(output_srt, "w", encoding="utf-8") as f:
                total_seg = len(result['segments'])
                for i, segment in enumerate(result['segments']):
                    start = self.format_timestamp(segment['start'])
                    end = self.format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    if precisa_traduzir:
                        try:
                            text = tradutor.translate(text)
                        except: pass
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
                    
                    if i % 5 == 0:
                        prog = int((i / total_seg) * 100)
                        self.status_sistema_var.set(f"Gerando Legenda: {prog}%")

            self.status_sistema_var.set("Concluído!")
            self.log("SUCESSO COMPLETO!")
            messagebox.showinfo("Concluído", f"Legenda salva:\n{output_srt}")

        except Exception as e:
            sys.stderr = stderr_original # Garante que restaura mesmo se der erro
            self.status_sistema_var.set("Erro Fatal")
            self.log(f"ERRO: {str(e)}")
            messagebox.showerror("Erro", str(e))
        
        finally:
            sys.stderr = stderr_original
            self.btn_run.config(state="normal", text="🚀 INICIAR PROCESSO")

if __name__ == "__main__":
    # Garante que funciona como EXE
    if getattr(sys, 'frozen', False):
        caminho_base = os.path.dirname(sys.executable)
        os.environ["PATH"] += os.pathsep + caminho_base
    
    # Se não tiver console (modo janela), cria um redirecionador vazio padrão para inicio
    if sys.stderr is None: 
        class NullWriter:
            def write(self, s): pass
            def flush(self): pass
        sys.stderr = NullWriter()

    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()