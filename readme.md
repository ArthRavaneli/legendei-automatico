# 🎬 Gerador de Legendas Pro IA

Aplicação desktop para gerar e traduzir legendas automaticamente utilizando a inteligência do **OpenAI Whisper**.

<p align="center">
  <img src="imagens_readme/Interface principal.png" width="80%" style="border-radius: 8px;" alt="Interface Principal">
</p>

### ✨ Funcionalidades
- **Transcrição e Tradução:** Converta áudio em legendas traduzidas.
- **Flexibilidade:** Escolha entre precisão (modelo `Large`) ou velocidade (modelo `Tiny`).
- **Controle:** Interface com logs detalhados, suporte a GPU e cancelamento seguro.

---

## 🚀 Como Começar

### 1. Instalação
```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/NOME_DO_REPO.git

# Instale as dependências
pip install openai-whisper torch deep-translator pyinstaller
```

### 2. O Passo Crucial: FFmpeg ⚠️
Para o programa funcionar, ele precisa do motor de áudio.
> **Simples:** Baixe o `ffmpeg.exe` e jogue dentro da pasta do projeto (https://www.gyan.dev/ffmpeg/builds/). 

> Baixe o **"ffmpeg-git-essentials.7z"**

> **Avançado:** Ou instale-o nas variáveis de ambiente do Windows.

### 3. Rodando
```bash
python interface_legenda.py
```
 Basta selecionar o vídeo, escolher o idioma e clicar em **Iniciar**. A legenda `.srt` aparecerá ao lado do vídeo original.

---

<details>
<summary>📦 <strong>Clique aqui para ver como criar o EXECUTÁVEL (.exe)</strong></summary>

Se você deseja compilar o projeto, é necessário um comando específico para incluir os arquivos do Whisper. Certifique-se de ter o `icone.ico` na raiz.

Execute no terminal:
```bash
pyinstaller --noconfirm --onefile --windowed --icon=icone.ico --add-data "icone.ico;." --collect-all whisper --collect-all deep_translator "interface_legenda.py"
```
O arquivo final estará na pasta `dist/`.
</details>

<details>
<summary>🔧 <strong>Solução de Problemas Comuns (Troubleshooting)</strong></summary>

| Problema | Causa Provável | Solução |
| :--- | :--- | :--- |
| **Erro [WinError 2]** | FFmpeg não encontrado | Baixe o `ffmpeg.exe` e coloque na mesma pasta do script/exe. |
| **Travou no início** | Download do Modelo | Na primeira vez, o Whisper baixa arquivos grandes (até 3GB). Aguarde o log. |

</details>

---

## 📄 Licença
Este projeto está sob a licença MIT.