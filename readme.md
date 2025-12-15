# 🎬 Gerador de Legendas Pro IA (Whisper)

Um aplicativo de desktop robusto desenvolvido em Python para gerar e traduzir legendas de vídeos automaticamente usando a inteligência artificial **OpenAI Whisper**.

<p align="center">
  <img src="imagens_readme/Interface principal.png" width="90%">
</p>

## ✨ Funcionalidades

* **Transcrição Automática:** Utiliza o modelo Whisper (OpenAI) para converter áudio em texto com alta precisão.
* **Tradução Integrada:** Traduz legendas automaticamente (ex: Inglês -> Português) usando o Google Translator.
* **Aceleração de Hardware:** Suporte a **GPU (NVIDIA CUDA)** para transcrições ultra-rápidas ou modo CPU para compatibilidade.
* **Modelos Selecionáveis:** Desde o `tiny` (rápido) até o `large` (preciso).
* **Interface Gráfica (GUI):** Interface amigável feita com Tkinter, com logs em tempo real e barra de progresso.
* **Monitoramento Real:** Exibe porcentagem de transcrição e status de download de modelos.
* **Botão de Pânico:** Funcionalidade de "Cancelar Operação" que interrompe o processo com segurança.

---

## 🛠️ Pré-requisitos

Para rodar este projeto, você precisará de:

1.  **Python 3.10 ou superior** instalado.
2.  **FFmpeg** (Essencial para processamento de áudio).
3.  **Drivers NVIDIA (Opcional):** Se desejar usar a GPU, instale o [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).


---

## ⚙️ Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/NOME_DO_REPO.git
cd NOME_DO_REPO
```

### 2. Configurar o Ambiente Virtual (Recomendado)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install openai-whisper torch deep-translator
pip install pyinstaller  # Apenas se for gerar o executável
```
*(Nota: O `tkinter` já vem instalado por padrão no Python).*

---

## 🚨 O Passo Importante: FFmpeg

O **FFmpeg** é o motor que o Whisper usa para ler o áudio dos arquivos de vídeo. Sem ele, o programa dará erro.

### Como instalar:

**Opção A (Fácil - Para usuários do Executável):**
Basta baixar o arquivo `ffmpeg.exe` e colocá-lo na **mesma pasta** onde está o `interface_legenda.py` (ou o `.exe`).

**Opção B (Recomendada - Variável de Sistema):**
1. Baixe o FFmpeg no site oficial (versão *essentials* build).
2. Extraia a pasta.
3. Adicione a pasta `bin` do FFmpeg nas **Variáveis de Ambiente (PATH)** do Windows.

---

## 🚀 Como Usar

1. Execute o script:
   ```bash
   python interface_legenda.py
   ```
2. **Passo 1:** Clique em "Procurar..." e selecione seu vídeo (`.mp4`, `.mkv`, etc).
3. **Passo 2:** Escolha as configurações:
   * **Processamento:** Use GPU se tiver placa NVIDIA (muito mais rápido).
   * **Modelo:** `Small` é o melhor equilíbrio. `Large` é o mais preciso (mas pesado).
   * **Idiomas:** Selecione o idioma do áudio original e para qual idioma deseja traduzir.
4. Clique em **Iniciar Processo**.
5. O arquivo `.srt` será salvo na mesma pasta do vídeo original.

---

## 📦 Como Criar o Executável (.exe)

Se você deseja distribuir o programa para quem não tem Python instalado, utilize o **PyInstaller**. 

⚠️ **Atenção:** Devido à complexidade do Whisper e bibliotecas de tradução, use o comando exato abaixo para evitar erros de arquivos faltando (`mel_filters.npz`, etc).

Certifique-se de ter um arquivo `icone.ico` na pasta do projeto.

```bash
pyinstaller --noconfirm --onefile --windowed --icon=icone.ico --add-data "icone.ico;." --collect-all whisper --collect-all deep_translator "interface_legenda.py"
```

O executável será gerado na pasta `dist/`.

---

## ⚠️ Problemas Comuns (Troubleshooting)

**Erro: "FileNotFoundError: [WinError 2]"**
* **Causa:** O sistema não encontrou o FFmpeg.
* **Solução:** Baixe o `ffmpeg.exe` e coloque na mesma pasta do programa, ou instale-o no PATH do Windows.

**Programa trava/congela no início**
* **Causa:** Na primeira execução de um modelo (ex: `large`), o Whisper baixa arquivos gigantes (3GB+).
* **Solução:** Aguarde. A interface mostrará o progresso do download no Log.

**Ícone não aparece na barra de tarefas**
* **Solução:** Se você recriou o `.exe`, o Windows pode estar usando cache. Mova o executável para outra pasta ou renomeie-o.

---

## 📄 Licença

Este projeto está sob a licença MIT. Sinta-se livre para usar e modificar.