"""End-to-end commercial and account checks in a disposable local database."""

from pathlib import Path
import os, subprocess, uuid, time, re, json, urllib.request, tempfile
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
settings = dict(
    l.split("=", 1)
    for l in (root / ".env").read_text().splitlines()
    if "=" in l and not l.startswith("#")
)
name = "p4_commercial_test_" + uuid.uuid4().hex[:8]
env = {
    **os.environ,
    "DATABASE_URL": f"postgresql+psycopg://p4:{settings['POSTGRES_PASSWORD']}@127.0.0.1:55432/{name}",
    "APP_ENV": "test",
    "ALLOW_DEMO": "1",
    "FRONTEND_DIST": str(root / "frontend/dist"),
}
python = str(root / ".venv/bin/python")
server = None
created = False
BASE = "http://127.0.0.1:8003"


def docker(*args):
    subprocess.run(
        [
            "docker",
            "--host=unix:///var/run/docker.sock",
            "compose",
            "exec",
            "-T",
            "db",
            *args,
        ],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )


checks = []
try:
    docker("createdb", "-U", "p4", name)
    created = True
    subprocess.run(
        [python, "-m", "alembic", "upgrade", "head"],
        cwd=root / "backend",
        env=env,
        check=True,
    )
    output = subprocess.check_output(
        [python, "-m", "app.cli", "demo"], cwd=root / "backend", env=env, text=True
    )
    credentials = {}
    for role, phone, password in re.findall(r"FICTÍCIO (\w+): (\+\d+) / (.+)", output):
        if role not in credentials:
            credentials[role] = (phone, password)
    subprocess.run(
        [python, "-m", "app.cli", "seed-course"],
        cwd=root / "backend",
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    with tempfile.TemporaryFile() as log:
        server = subprocess.Popen(
            [
                python,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8003",
                "--no-access-log",
            ],
            cwd=root / "backend",
            env=env,
            stdout=log,
            stderr=log,
        )
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + "/api/health", timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("Servidor não ficou pronto.")
        with sync_playwright() as pw:
            api = pw.request.new_context(base_url=BASE)
            student_login = api.post(
                "/api/auth/login",
                data={
                    "phone": credentials["aluno"][0],
                    "password": credentials["aluno"][1],
                },
            ).json()
            sid = student_login["user"]["id"]
            csrf = {"X-CSRF-Token": student_login["csrf"]}
            plan = api.get("/api/plans/" + str(sid)).json()
            plan.pop("id")
            plan.pop("user_id")
            plan["entries"] = [
                {
                    "key": "income",
                    "category": "rendas",
                    "label": "Renda de teste",
                    "month": plan["start"],
                    "forecast": "3000.00",
                    "actual": None,
                    "deducted": False,
                    "method": "outro",
                    "absent": False,
                },
                {
                    "key": "expense",
                    "category": "fixas",
                    "label": "Despesa de teste",
                    "month": plan["start"],
                    "forecast": "1000.00",
                    "actual": None,
                    "deducted": False,
                    "method": "outro",
                    "absent": False,
                },
            ]
            assert (
                api.put("/api/plans/" + str(sid), data=plan, headers=csrf).status == 200
            )
            c = api.post(
                "/api/auth/login",
                data={
                    "phone": credentials["consultor"][0],
                    "password": credentials["consultor"][1],
                },
            ).json()
            assert (
                api.post(
                    "/api/notes/" + str(sid),
                    data={"text": "INTERNO_NAO_VISIVEL_NO_COMERCIAL", "internal": True},
                    headers={"X-CSRF-Token": c["csrf"]},
                ).status
                == 200
            )
            assert (
                api.post(
                    "/api/notes/" + str(sid),
                    data={"text": "Orientação de teste liberada.", "internal": False},
                    headers={"X-CSRF-Token": c["csrf"]},
                ).status
                == 200
            )
            browser = pw.chromium.launch(
                executable_path="/usr/bin/chromium", args=["--no-sandbox"]
            )
            ctx = browser.new_context(
                viewport={"width": 1440, "height": 1050}, reduced_motion="reduce"
            )
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept())

            def login(role):
                page.goto(BASE)
                page.get_by_label("Celular com DDD").fill(credentials[role][0])
                page.get_by_label("Senha", exact=True).fill(credentials[role][1])
                page.get_by_role("button", name="Entrar na minha conta").click()
                expect(page.get_by_role("button", name="Sair da conta")).to_be_visible()

            login("administrador")
            page.get_by_role("button", name="Administração", exact=True).click()
            page.get_by_role("button", name="Equipe e perfis", exact=True).click()
            expect(
                page.get_by_role("heading", name="Novo integrante da equipe")
            ).to_be_visible()
            assert page.get_by_text("Maria · conta fictícia", exact=True).count() == 0
            assert page.get_by_role("checkbox", name="aluno", exact=True).count() == 0
            page.get_by_label("Nome completo", exact=True).fill(
                "Equipe fictícia adicional"
            )
            page.get_by_label("Celular com DDD (+55 automático)", exact=False).fill(
                "11900000009"
            )
            page.get_by_label("Senha inicial (6 a 200 caracteres)", exact=True).fill(
                "627491"
            )
            page.get_by_role("button", name="Salvar cadastro", exact=True).click()
            summary = page.locator("summary").filter(
                has_text="Equipe fictícia adicional"
            )
            expect(summary).to_be_visible()
            summary.click()
            page.get_by_role("button", name="Editar integrante", exact=True).click()
            form = page.get_by_role("form", name="Editar cadastro da equipe")
            form.get_by_label("Nome completo").fill("Equipe fictícia revisada")
            form.get_by_role("button", name="Salvar alterações").click()
            expect(
                page.locator("summary").filter(has_text="Equipe fictícia revisada")
            ).to_be_visible()
            checks.append("cadastro e edição da equipe separados dos alunos")
            page.get_by_role("button", name="Minha conta e ajuda", exact=True).click()
            assert page.get_by_label("Senha atual", exact=True).count() == 0
            page.get_by_role("button", name="Trocar senha", exact=True).click()
            expect(page.get_by_label("Senha atual", exact=True)).to_be_visible()
            help_panel = page.locator("section").filter(
                has=page.get_by_role(
                    "heading", name="Estamos aqui para ajudar.", exact=True
                )
            )
            assert help_panel.get_by_label("Senha atual", exact=True).count() == 0
            checks.append("troca de senha em painel próprio aberto por botão")
            page.get_by_role("button", name="Sair da conta").click()
            login("vendedor")
            expect(
                page.get_by_role("heading", name="Comercial", exact=True)
            ).to_be_visible()
            page.get_by_role(
                "button", name="Adicionar alunos à fila", exact=True
            ).click()
            expect(page.get_by_role("status")).to_contain_text("2 alunos adicionados")
            checks.append("dashboard comercial e fila explícita de alunos")
            page.get_by_role("button", name="Fila de consultorias", exact=True).click()
            page.get_by_label("Buscar aluno", exact=True).fill("Maria")
            expect(
                page.get_by_role("button", name="Abrir consultoria", exact=True)
            ).to_have_count(1)
            page.get_by_role("button", name="Abrir consultoria", exact=True).click()
            editor = page.locator("section.sales-editor")
            editor.get_by_role(
                "button", name="Consultar planejamento financeiro", exact=True
            ).click()
            expect(editor.get_by_text("R$ 2.000,00", exact=True).first).to_be_visible()
            expect(
                editor.get_by_text("Orientação de teste liberada.", exact=True)
            ).to_be_visible()
            assert (
                page.get_by_text("INTERNO_NAO_VISIVEL_NO_COMERCIAL", exact=True).count()
                == 0
            )
            assert page.request.get(BASE + "/api/plans/" + str(sid)).status == 403
            checks.append("visão financeira comercial sem edição e sem notas internas")
            editor.get_by_label("Etapa comercial", exact=False).select_option(
                "proposta"
            )
            me = page.request.get(BASE + "/api/auth/me").json()
            editor.get_by_label("Responsável", exact=False).select_option(
                str(me["user"]["id"])
            )
            editor.get_by_label("Condição aceita", exact=False).select_option(
                "installments"
            )
            editor.get_by_label("Atendimento, aulas indicadas e próximos passos").fill(
                "Teste: organizar os dados e indicar aulas revisadas. Proposta parcelada em avaliação."
            )
            editor.get_by_role(
                "button", name="Salvar atendimento comercial", exact=True
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Atendimento comercial salvo"
            )
            checks.append(
                "registro de proposta com preço à vista e total parcelado distintos"
            )
            page.get_by_role("button", name="Agendar reunião", exact=True).click()
            booking = page.locator("form.sales-editor")
            booking.get_by_label("Data e horário · Brasília", exact=True).fill(
                "2027-01-10T12:00"
            )
            expect(booking.get_by_label("Duração em minutos")).to_have_value("45")
            booking.get_by_role("button", name="Salvar reunião", exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Agenda atualizada")
            page.get_by_role("button", name="Agenda", exact=True).click()
            expect(
                page.get_by_text("Maria · conta fictícia", exact=True)
            ).to_be_visible()
            page.get_by_role("button", name="Editar reunião", exact=True).click()
            booking = page.locator("form.sales-editor")
            booking.get_by_label("Situação da reunião", exact=False).select_option(
                "realizada"
            )
            booking.get_by_role("button", name="Salvar reunião", exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Agenda atualizada")
            checks.append("agenda de 45 minutos e registro de consultoria realizada")
            page.get_by_role("button", name="Kanban", exact=True).click()
            column = page.locator(".stage-proposta")
            expect(
                column.get_by_text("Maria · conta fictícia", exact=True)
            ).to_be_visible()
            column.get_by_role("button", name="Abrir atendimento", exact=True).click()
            editor = page.locator("section.sales-editor")
            editor.get_by_label("Etapa comercial", exact=False).select_option("ganho")
            editor.get_by_role(
                "button", name="Salvar atendimento comercial", exact=True
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Atendimento comercial salvo"
            )
            page.get_by_role("button", name="Dashboard", exact=True).click()
            metric = page.locator(".sales-metrics .stat").filter(
                has_text="Valor nominal dos contratos"
            )
            expect(metric.get_by_text("R$ 5.964,00", exact=True)).to_be_visible()
            checks.append(
                "kanban e venda registrada pelo valor nominal sem confirmação de recebimento"
            )
            page.get_by_role("button", name="Análises e relatórios", exact=True).click()
            with page.expect_download() as result:
                page.get_by_role("link", name="Exportar funil completo CSV").click()
            assert result.value.suggested_filename == "comercial-p4.csv"
            checks.append("relatório comercial e exportação CSV protegida")
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            page.screenshot(path="/tmp/p4-commercial-mobile.png", full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1050})
            page.get_by_role("button", name="Dashboard", exact=True).click()
            page.screenshot(path="/tmp/p4-commercial-dashboard.png", full_page=True)
            checks.append("área comercial sem rolagem horizontal no celular")
            page.get_by_role("button", name="Sair da conta").click()
            login("aluno")
            page.get_by_role("button", name="Minha conta e ajuda", exact=True).click()
            expect(
                page.get_by_role("heading", name="Histórico do acesso", exact=True)
            ).to_be_visible()
            cadaster = page.locator("section").filter(
                has=page.get_by_role("heading", name="Meu cadastro", exact=True)
            )
            assert cadaster.get_by_text("Histórico do acesso", exact=True).count() == 0
            checks.append("histórico anual separado do cadastro do aluno")
            page.get_by_role("button", name="Meu relatório", exact=True).click()
            guidance = page.locator(".guidance-card")
            expect(
                guidance.get_by_role(
                    "heading", name="Orientações da consultoria", exact=True
                )
            ).to_be_visible()
            assert (
                float(
                    guidance.get_by_role("heading")
                    .evaluate("(e)=>getComputedStyle(e).fontSize")
                    .replace("px", "")
                )
                == 17
            )
            with page.expect_download() as pdf:
                page.get_by_role("link", name="Baixar PDF", exact=True).click()
            from pypdf import PdfReader

            text = PdfReader(pdf.value.path()).pages[0].extract_text()
            assert (
                "Orientação de teste liberada." in text
                and "INTERNO_NAO_VISIVEL_NO_COMERCIAL" not in text
            )
            assert text.index("Orientação de teste liberada.") < text.index("Entradas")
            checks.append("orientações compactas na tela e no início do PDF")
            assert not errors, errors
            browser.close()
            api.dispose()
    print(
        json.dumps(
            {"passed": checks, "javascript_errors": errors},
            ensure_ascii=False,
            indent=2,
        )
    )
finally:
    if server:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
    if created:
        docker("dropdb", "-U", "p4", name)
