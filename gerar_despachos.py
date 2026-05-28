#!/usr/bin/env python3
"""
Gera despachos pré-preenchidos para os 6 links da seção "Resoluções nº 22 e 198".
Para cada página: preenche campos fictícios, executa atualizar(), extrai o texto,
salva em .txt e gera PDF via printDiv (equivalente ao botão Imprimir → Salvar como PDF).
"""

import os
import subprocess
import re
import base64
import tempfile

PROJECT_DIR = os.path.expanduser("~/relato-main")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "despachos_gerados")

PAGINAS = [
    ("ausencia_registro_cau_pj_22_198.html",
     "01_ausencia_registro_cau_pj",
     "Construtora Arco & Plano Ltda.",
     "CEP-2024-0001-SP"),

    ("ausencia_registro_cau_e_crea_pj_22_198.html",
     "02_ausencia_registro_cau_e_crea_pj",
     "Studio Design Ambiental Ltda.",
     "CEP-2024-0002-SP"),

    ("ausencia_responsavel_tecnico_pj_22_198.html",
     "03_ausencia_responsavel_tecnico_pj",
     "Reforma & Cia Engenharia Ltda.",
     "CEP-2024-0003-SP"),

    ("exercicio_ilegal_profissao_pf_ausencia_responsavel_atividade_22_198.html",
     "04_exercicio_ilegal_pf_ausencia_responsavel",
     "João Carlos Mendonça",
     "CEP-2024-0004-SP"),

    ("exercicio_ilegal_profissao_pf_exploracao_economica_198_22_198.html",
     "05_exercicio_ilegal_pf_exploracao_economica",
     "Maria Fernanda Oliveira Santos",
     "CEP-2024-0005-SP"),

    ("ausencia_rrt_pf_22_198.html",
     "06_ausencia_rrt_pf",
     "Roberto Alves Pereira",
     "CEP-2024-0006-SP"),
]

# Script injetado em cada página para preencher o formulário e chamar atualizar()
# Execução SÍNCRONA — inserido depois de todos os scripts CDN e inline do body.
INJECT_SCRIPT = """
<script id="__auto_fill__">
(function() {
    // Impede alert() de bloquear a execução
    window.alert = function(msg) {
        var err = document.createElement('pre');
        err.id = '__alert_msg__';
        err.style.display = 'none';
        err.textContent = msg;
        document.body.appendChild(err);
    };

    try {
        // ── Dados do Processo ──────────────────────────────────────
        document.getElementById('input_num_processo').value  = '__PROCESSO__';
        document.getElementById('input_interessado').value   = '__INTERESSADO__';

        // Relator: Renata Ballone (value=F, índice 2)
        var relator = document.getElementById('input_relator');
        relator.selectedIndex = 2;
        if (typeof inserirAssinaturas === 'function') inserirAssinaturas();

        // Origem da demanda: denúncia (índice 1)
        var origem = document.getElementById('select_origem_demanda');
        if (origem) origem.selectedIndex = 1;

        // ── Histórico ─────────────────────────────────────────────
        document.getElementById('input_dt_relatorio_fisc').value         = '10/01/2024';
        document.getElementById('input_dt_notificacao_preventiva').value = '20/01/2024';

        // Devolução de correspondência (Notif. Preventiva): Sim
        var simNP = document.getElementById('input_devolucao_corresp_sim');
        simNP.checked = true;
        simNP.dispatchEvent(new Event('change'));
        var tentNP = document.getElementById('input_corresp_devolvida_sim_1');
        if (tentNP) tentNP.selectedIndex = 1;   // 1 tentativa de envio
        var meioNP = document.getElementById('select_corresp_devolvida_sim');
        if (meioNP) meioNP.selectedIndex = 6;   // por ciência eletrônica pelo SICCAU
        var dtNP = document.getElementById('input_corresp_devolvida_sim_2');
        if (dtNP) dtNP.value = '30/01/2024';

        // Contestação da Notificação Preventiva: não (deixa desmarcado)

        // Tentativa de regularização: Não
        var tentNao = document.getElementById('input_tentativa_regularizacao_nao');
        if (tentNao) { tentNao.checked = true; tentNao.dispatchEvent(new Event('change')); }

        // Data do Auto de Infração
        document.getElementById('input_dt_auto').value = '10/02/2024';

        // Devolução de correspondência (Auto): Sim
        var simAI = document.getElementById('input_devolucao_corresp_auto_sim');
        simAI.checked = true;
        simAI.dispatchEvent(new Event('change'));
        var tentAI = document.getElementById('input_corresp_auto_devolvida_sim_1');
        if (tentAI) tentAI.selectedIndex = 1;   // 1 tentativa de envio
        var meioAI = document.getElementById('select_corresp_auto_devolvida_sim');
        if (meioAI) meioAI.selectedIndex = 6;   // por ciência eletrônica pelo SICCAU
        var dtAI = document.getElementById('input_corresp_auto_devolvida_sim_2');
        if (dtAI) dtAI.value = '28/02/2024';

        // Encaminhamento: Processo à Revelia
        var rev = document.getElementById('input_processo_revelia');
        if (rev) { rev.checked = true; rev.dispatchEvent(new Event('change')); }

        // ── Análises e Considerações ──────────────────────────────
        // Sem regularização e sem pagamento de multa (páginas 1-4, 6)
        var semReg = document.getElementById('input_sem_regularizacao_sem_pagamento');
        if (semReg && !semReg.disabled) { semReg.checked = true; semReg.dispatchEvent(new Event('change')); }
        // Página 05: "Houve pagamento da multa?" → Não
        var pagNao = document.getElementById('input_somente_pagamento_multa_nao');
        if (pagNao) { pagNao.checked = true; pagNao.dispatchEvent(new Event('change')); }

        // ── Voto ─────────────────────────────────────────────────
        // Alteração de multa: Não
        var altNao = document.getElementById('input_alteracao_multa_nao');
        if (altNao) { altNao.checked = true; altNao.dispatchEvent(new Event('change')); }

        // ── Executa o botão Atualizar ─────────────────────────────
        if (typeof atualizar === 'function') atualizar();

        // ── Captura o texto gerado ────────────────────────────────
        var out = document.getElementById('conteudo_relato_final');
        var texto = out ? out.innerText : '(elemento não encontrado)';

        // Também inclui a tabela de cabeçalho
        var tab = document.getElementById('tab_cabecalho_final');
        var cabecalho = tab ? tab.innerText : '';

        var wrapper = document.createElement('pre');
        wrapper.id = '__despacho_output__';
        wrapper.style.display = 'none';
        wrapper.textContent = cabecalho + '\\n\\n' + texto;
        document.body.appendChild(wrapper);

        // ── Captura o HTML de impressão (equivalente ao botão Imprimir) ──
        // Intercepta window.open() para capturar o conteúdo que printDiv escreve na janela popup
        var printHTML = '';
        var fakeWin = null;
        window.open = function() {
            fakeWin = {
                document: {
                    write: function(s) { printHTML += s; },
                    close: function() {}
                },
                print: function() {},
                onload: null
            };
            return fakeWin;
        };
        if (typeof printDiv === 'function') printDiv('div_relato_final');
        // printDiv define fakeWin.onload depois de document.close(); chama manualmente
        if (fakeWin && fakeWin.onload) fakeWin.onload();

        // Codifica em base64 para evitar problemas com HTML entities no DOM dump
        var printB64 = btoa(unescape(encodeURIComponent(printHTML)));
        var printStore = document.createElement('div');
        printStore.id = '__print_html_b64__';
        printStore.style.display = 'none';
        printStore.textContent = printB64;
        document.body.appendChild(printStore);

    } catch(e) {
        var errEl = document.createElement('pre');
        errEl.id = '__despacho_error__';
        errEl.style.display = 'none';
        errEl.textContent = 'ERRO: ' + e.toString() + '\\n' + (e.stack || '');
        document.body.appendChild(errEl);
    }
})();
</script>
"""

def html_to_text(s):
    """Remove tags HTML básicas e limpa espaços."""
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'&amp;', '&', s)
    s = re.sub(r'&lt;', '<', s)
    s = re.sub(r'&gt;', '>', s)
    return s.strip()

def extrair_tag(html, tag_id):
    """Extrai o conteúdo de um elemento pelo seu ID."""
    pattern = r'id=["\']' + re.escape(tag_id) + r'["\'][^>]*>(.*?)</(?:pre|div|p|span|strong)\b'
    m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if m:
        return html_to_text(m.group(1))
    return None

def criar_html_modificado(html_original, processo, interessado):
    """Insere o script de automação e substitui placeholders."""
    script = INJECT_SCRIPT.replace('__PROCESSO__', processo).replace('__INTERESSADO__', interessado)
    # Insere antes do ÚLTIMO </body> (o primeiro ocorre dentro de uma string JS)
    last_body = html_original.rfind('</body>')
    html_mod = html_original[:last_body] + script + '\n' + html_original[last_body:]
    return html_mod

def rodar_chromium_headless(html_path):
    """Roda Chromium headless e retorna o dump do DOM."""
    cmd = [
        'chromium',
        '--headless=old',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--dump-dom',
        f'file://{html_path}',
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return resultado.stdout

def rodar_chromium_pdf(html_path, pdf_path):
    """Roda Chromium headless e salva a página como PDF."""
    cmd = [
        'chromium',
        '--headless=old',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--print-to-pdf-no-header',
        f'--print-to-pdf={pdf_path}',
        f'file://{html_path}',
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return resultado.returncode == 0

def processar_pagina(nome_arquivo, nome_saida, interessado, processo):
    html_src = os.path.join(PROJECT_DIR, nome_arquivo)
    print(f"\n{'='*60}")
    print(f"Processando: {nome_arquivo}")
    print(f"{'='*60}")

    with open(html_src, 'r', encoding='utf-8') as f:
        html_original = f.read()

    html_mod = criar_html_modificado(html_original, processo, interessado)

    # Salva em arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False,
                                     encoding='utf-8', dir='/tmp') as tmp:
        tmp.write(html_mod)
        tmp_path = tmp.name

    try:
        print(f"  → Executando Chromium headless...")
        dom = rodar_chromium_headless(tmp_path)

        # Procura o elemento de saída
        despacho = extrair_tag(dom, '__despacho_output__')
        erro     = extrair_tag(dom, '__despacho_error__')
        alerta   = extrair_tag(dom, '__alert_msg__')

        if erro:
            print(f"  ✗ Erro JavaScript: {erro[:300]}")
        if alerta:
            print(f"  ⚠ Validação: {alerta[:300]}")

        if despacho:
            # Salva no arquivo de saída
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            out_path = os.path.join(OUTPUT_DIR, f"{nome_saida}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(despacho)
            print(f"  ✓ Despacho salvo em: despachos_gerados/{nome_saida}.txt")
            print(f"  → Primeiras linhas:")
            for linha in despacho.splitlines()[:6]:
                if linha.strip():
                    print(f"     {linha.strip()[:80]}")

            # Gera PDF a partir do HTML capturado de printDiv
            print_b64 = extrair_tag(dom, '__print_html_b64__')
            if print_b64:
                try:
                    print_html = base64.b64decode(print_b64.strip().encode()).decode('utf-8')
                    # printDiv usa caminhos relativos para as imagens; converte para file:// absoluto
                    img_dir = os.path.join(PROJECT_DIR, 'img')
                    print_html = print_html.replace(
                        'src="img/cabecalho.jpg"',
                        f'src="file://{img_dir}/cabecalho.jpg"'
                    ).replace(
                        'src="img/rodape.jpg"',
                        f'src="file://{img_dir}/rodape.jpg"'
                    )
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False,
                                                     encoding='utf-8', dir='/tmp') as ptmp:
                        ptmp.write(print_html)
                        ptmp_path = ptmp.name
                    try:
                        print(f"  → Gerando PDF...")
                        pdf_path = os.path.join(OUTPUT_DIR, f"{nome_saida}.pdf")
                        if rodar_chromium_pdf(ptmp_path, pdf_path):
                            print(f"  ✓ PDF salvo em: despachos_gerados/{nome_saida}.pdf")
                        else:
                            print(f"  ✗ Falha ao gerar PDF (Chromium retornou erro).")
                    finally:
                        os.unlink(ptmp_path)
                except Exception as e:
                    print(f"  ✗ Erro ao gerar PDF: {e}")
            else:
                print(f"  ✗ HTML de impressão não capturado (printDiv não executou).")
        else:
            print(f"  ✗ Elemento '__despacho_output__' não encontrado no DOM.")
            # Tenta buscar diretamente conteudo_relato_final no dump
            fallback = extrair_tag(dom, 'conteudo_relato_final')
            if fallback:
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                out_path = os.path.join(OUTPUT_DIR, f"{nome_saida}.txt")
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(fallback)
                print(f"  ✓ (fallback) Despacho salvo em: despachos_gerados/{nome_saida}.txt")
            else:
                print(f"  ✗ Não foi possível extrair o despacho.")
                # Salva o DOM bruto para diagnóstico
                diag_path = os.path.join(OUTPUT_DIR, f"{nome_saida}_dom_dump.html")
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                with open(diag_path, 'w', encoding='utf-8') as f:
                    f.write(dom)
                print(f"  → DOM dump diagnóstico salvo.")
    finally:
        os.unlink(tmp_path)

def main():
    print(f"Diretório de saída: {OUTPUT_DIR}")
    for args in PAGINAS:
        processar_pagina(*args)
    print(f"\n{'='*60}")
    print("Concluído.")
    arquivos = os.listdir(OUTPUT_DIR) if os.path.exists(OUTPUT_DIR) else []
    print(f"Arquivos gerados ({len(arquivos)}): {', '.join(sorted(arquivos))}")

if __name__ == '__main__':
    main()
