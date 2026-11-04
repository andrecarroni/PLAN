"""Exercise profile editing in a disposable PostgreSQL database and local browser."""

from pathlib import Path
import os, subprocess, uuid, time, json, re, urllib.request, tempfile
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
settings = dict(
    l.split("=", 1)
    for l in (root / ".env").read_text().splitlines()
    if "=" in l and not l.startswith("#")
)
name = "p4_profile_test_" + uuid.uuid4().hex[:10]
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


def docker(*args):
    return subprocess.run(
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
    match = re.search(r"FICTÍCIO administrador: (\+\d+) / (.+)", output)
    assert match
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
                "8002",
                "--no-access-log",
            ],
            cwd=root / "backend",
            env=env,
            stdout=log,
            stderr=log,
        )
        for _ in range(50):
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:8002/api/health", timeout=1
                ) as r:
                    assert json.load(r) == {"status": "ok"}
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("Servidor de teste não ficou pronto.")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path="/usr/bin/chromium", args=["--no-sandbox"]
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept())
            page.goto("http://127.0.0.1:8002")
            page.get_by_label("Celular com DDD").fill(match[1])
            page.get_by_label("Senha", exact=True).fill(match[2])
            page.get_by_role("button", name="Entrar na minha conta").click()
            page.get_by_role("button", name="Alunos e atendimentos", exact=True).click()
            page.get_by_label("Buscar aluno").fill("Maria")
            expect(
                page.get_by_role("button", name="Editar cadastro", exact=True)
            ).to_have_count(1)
            page.get_by_role("button", name="Editar cadastro", exact=True).click()
            form = page.get_by_role("form", name="Editar cadastro do aluno")
            form.get_by_label("Nome completo").fill("Aluno fictício revisado")
            form.get_by_label("E-mail, opcional").fill("revisado@example.com")
            page.route("**/api/users/*/profile", lambda route: route.abort())
            form.get_by_role("button", name="Salvar alterações").click()
            expect(form.get_by_role("alert")).to_contain_text(
                "Não foi possível conectar"
            )
            expect(form.get_by_label("Nome completo")).to_have_value(
                "Aluno fictício revisado"
            )
            page.unroute("**/api/users/*/profile")
            form.get_by_role("button", name="Salvar alterações").click()
            expect(page.get_by_role("status")).to_contain_text(
                "Cadastro atualizado com sucesso."
            )
            page.get_by_label("Buscar aluno").fill("Aluno fictício revisado")
            expect(
                page.get_by_text("revisado@example.com", exact=False)
            ).to_be_visible()
            page.get_by_role("button", name="Editar cadastro", exact=True).click()
            form = page.get_by_role("form", name="Editar cadastro do aluno")
            form.get_by_label("Celular com DDD").fill("+5511999990003")
            form.get_by_role("button", name="Salvar alterações").click()
            expect(form.get_by_role("alert")).to_contain_text(
                "já pertence a outra conta"
            )
            expect(form.get_by_label("Celular com DDD")).to_have_value("+5511999990003")
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            form.get_by_role("button", name="Cancelar", exact=True).click()
            expect(form).to_have_count(0)
            assert not errors, errors
            browser.close()
    print(
        "Navegador: edição e atualização da lista; erro de rede preserva campos; duplicidade preserva campos; formulário mobile sem rolagem horizontal; cancelamento. Tudo passou."
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
