"""Functional checks against explicitly generated fictitious accounts only."""

import os, re, json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.getenv("P4_BASE_URL", "http://127.0.0.1:8000")
credentials = {}
for line in (
    Path(os.getenv("P4_DEMO_CREDENTIALS", "/tmp/p4-rebuild-demo.txt"))
    .read_text()
    .splitlines()
):
    m = re.match(r"FICTÍCIO (\w+): (\+\d+) / (.+)", line)
    if m and m[1] not in credentials:
        credentials[m[1]] = (m[2], m[3])
if not {"aluno", "administrador", "vendedor"}.issubset(credentials):
    raise SystemExit(
        "Forneça a saída protegida de app.cli demo, somente de banco fictício."
    )
checks = []
violations = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path=os.getenv("P4_BROWSER_PATH", "/usr/bin/chromium"),
        args=["--no-sandbox"],
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 1050})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())

    def login(role):
        page.goto(BASE)
        page.get_by_label("Celular com código do país").fill(credentials[role][0])
        page.get_by_label("Senha", exact=True).fill(credentials[role][1])
        page.get_by_role("button", name="Entrar na minha conta").click()
        expect(page.get_by_role("button", name="Sair da conta")).to_be_visible()

    def saved():
        expect(page.get_by_role("status")).to_contain_text("Salvo", timeout=15000)

    def audit(name):
        axe = Path(
            os.getenv("P4_AXE_PATH", "/tmp/p4-a11y/node_modules/axe-core/axe.min.js")
        )
        if not axe.is_file():
            return
        page.evaluate(axe.read_text())
        violations[name] = page.evaluate(
            "async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}"
        )

    login("aluno")
    checks.append("login real")
    me = page.request.get(BASE + "/api/auth/me").json()
    sid = me["user"]["id"]
    headers = {"X-CSRF-Token": me["csrf"]}

    def server_plan():
        return page.request.get(f"{BASE}/api/plans/{sid}").json()

    p = server_plan()
    p.pop("id")
    p.pop("user_id")
    p.update(
        start="2026-11",
        selected_month="2026-11",
        step=0,
        completed=[],
        entries=[],
        debts=[],
        goals=[],
    )
    assert (
        page.request.put(f"{BASE}/api/plans/{sid}", data=p, headers=headers).status
        == 200
    )
    page.reload()
    expect(page.get_by_role("heading", name="Rendas", exact=True)).to_be_visible()
    page.get_by_label("Novo item").fill("Renda líquida")
    page.get_by_role("button", name="Adicionar item", exact=True).click()
    page.get_by_label("Valor previsto").fill("6500,00")
    saved()
    checks.append("salvamento confirmado")
    page.route(
        "**/api/plans/*",
        lambda route: (
            route.abort() if route.request.method == "PUT" else route.continue_()
        ),
    )
    page.get_by_label("Valor previsto").fill("6600,00")
    expect(page.get_by_role("status")).to_contain_text(
        "Não foi possível salvar", timeout=15000
    )
    expect(page.get_by_label("Valor previsto")).to_have_value("6600,00")
    checks.append("falha de rede mantém o campo sem falso Salvo")
    page.unroute("**/api/plans/*")
    page.get_by_role("button", name="Tentar novamente", exact=True).click()
    saved()
    page.get_by_role("button", name="4 Despesas fixas").click()
    page.get_by_label("Novo item").fill("Assinaturas")
    page.get_by_role("button", name="Adicionar item", exact=True).click()
    page.get_by_label("Valor previsto").fill("200,00")
    saved()
    page.reload()
    expect(page.get_by_label("Valor previsto")).to_have_value("200,00")
    checks.append("persistência e retomada da etapa")
    audit("planejamento")
    page.screenshot(path="/tmp/p4-rebuilt-desktop.png", full_page=True)
    page.get_by_text("Repetir ou copiar valores", exact=True).click()
    page.get_by_label("Do mês").select_option("2026-12")
    page.get_by_label("Até o mês").select_option("2027-02")
    page.get_by_role("button", name="Repetir no intervalo", exact=True).click()
    saved()
    entries = server_plan()["entries"]
    expense = [e for e in entries if e["category"] == "fixas"]
    assert sorted(e["month"] for e in expense) == [
        "2026-11",
        "2026-12",
        "2027-01",
        "2027-02",
    ]
    checks.append("repetição respeita início e término entre anos")
    page.get_by_label("Mês do planejamento").select_option("2026-12")
    saved()
    page.get_by_label("Valores", exact=False).select_option("actual")
    page.get_by_label("Valor realizado").fill("175,00")
    saved()
    page.get_by_role("button", name="Copiar mês anterior", exact=True).click()
    saved()
    assert (
        next(
            e
            for e in server_plan()["entries"]
            if e["category"] == "fixas" and e["month"] == "2026-12"
        )["actual"]
        == "175.00"
    )
    checks.append("copiar previsto preserva realizado existente")
    page.get_by_label("Valores", exact=False).select_option("forecast")
    remote = server_plan()
    remote.pop("id")
    remote.pop("user_id")
    remote["entries"][0]["forecast"] = "6700.00"
    assert (
        page.request.put(f"{BASE}/api/plans/{sid}", data=remote, headers=headers).status
        == 200
    )
    page.get_by_label("Valor previsto").fill("210,00")
    expect(page.get_by_role("alert")).to_contain_text(
        "Outro dispositivo", timeout=15000
    )
    expect(page.get_by_label("Valor previsto")).to_have_value("210,00")
    assert (
        next(
            e
            for e in server_plan()["entries"]
            if e["category"] == "fixas" and e["month"] == "2026-12"
        )["forecast"]
        == "200.00"
    )
    checks.append("conflito não sobrescreve outro dispositivo")
    page.get_by_role("button", name="Recarregar dados do servidor", exact=True).click()
    expect(page.get_by_label("Valor previsto")).to_have_value("200,00")
    page.get_by_label("Valor previsto").fill("inválido")
    expect(page.get_by_role("status")).to_contain_text(
        "Não foi possível salvar", timeout=15000
    )
    expect(page.get_by_label("Valor previsto")).to_have_value("inválido")
    page.get_by_label("Valor previsto").fill("200,00")
    page.get_by_role("button", name="Tentar novamente", exact=True).click()
    saved()
    checks.append("valor inválido é preservado e rejeitado")
    page.get_by_role("button", name="Meu relatório", exact=True).click()
    expect(
        page.get_by_role("heading", name="Meu relatório", exact=True)
    ).to_be_visible()
    page.get_by_label("Mês selecionado").select_option("2026-11")
    expect(page.get_by_text("R$ 6.700,00", exact=True).first).to_be_visible()
    checks.append("relatório lê valores atuais do servidor")
    with page.expect_download() as download:
        page.get_by_role("link", name="Baixar PDF").click()
    assert download.value.suggested_filename == "planejamento-p4.pdf"
    checks.append("download PDF real")
    audit("relatorio")
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_role("button", name="Abrir menu").click()
    page.get_by_role("button", name="Meu planejamento", exact=True).click()
    expect(page.get_by_label("Valor previsto")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.get_by_role("button", name="Ampliar letras").click()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.screenshot(path="/tmp/p4-rebuilt-mobile.png", full_page=True)
    checks.append("celular e letras ampliadas sem rolagem horizontal")
    audit("celular")
    page.get_by_role("button", name="Sair da conta").click()
    page.set_viewport_size({"width": 1440, "height": 1050})
    login("administrador")
    page.get_by_role("button", name="Administração", exact=True).click()
    page.get_by_role("button", name="Conteúdos", exact=True).click()
    expect(page.get_by_text("Organize suas informações", exact=True)).to_be_visible()
    page.get_by_role("button", name="Revisar", exact=True).first.click()
    page.get_by_label("Situação do conteúdo").select_option("publicado")
    page.get_by_role("button", name="Salvar revisão", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Operação concluída")
    checks.append("revisão e publicação administrativa no banco fictício")
    audit("administracao")
    page.get_by_role("button", name="Sair da conta").click()
    login("vendedor")
    page.get_by_role("button", name="Alunos e atendimentos", exact=True).click()
    expect(page.get_by_label("Buscar aluno")).to_be_visible()
    assert page.get_by_role("button", name="Planejamento", exact=True).count() == 0
    assert page.request.get(f"{BASE}/api/plans/{sid}").status == 403
    checks.append("vendedor sem dados financeiros na interface e API")
    assert not errors, errors
    browser.close()
result = {"passed": checks, "javascript_errors": errors, "accessibility": violations}
print(json.dumps(result, ensure_ascii=False, indent=2))
Path("/tmp/p4-browser-results.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2)
)
if any(violations.values()):
    raise SystemExit("Há violações de acessibilidade a corrigir.")
