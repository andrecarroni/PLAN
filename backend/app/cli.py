import argparse, getpass, secrets, os
from sqlalchemy import select
from pydantic import ValidationError
from .db import SessionLocal
from .models import User, Category, Content, ContentVersion
from .schemas import UserInput
from .security import hash_password, audit, annual, now
from .finance import CATEGORIES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create-admin", "seed-course", "demo"])
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "create-admin":
            name = input("Nome completo: ")
            phone = input("Celular com DDD (+55 automático; outro país: +código): ")
            password = getpass.getpass("Senha (6 a 200 caracteres): ")
            if password != getpass.getpass("Confirme a senha: "):
                raise SystemExit("Senhas diferentes.")
            try:
                data = UserInput(
                    name=name, phone=phone, password=password, roles=["administrador"]
                )
            except ValidationError as exc:
                messages = {
                    "name": "Informe um nome com pelo menos 2 caracteres.",
                    "phone": "Informe DDD e número para Brasil (+55 automático). Para outro país, informe + e o código do país.",
                    "password": "Use uma senha de 6 a 200 caracteres; números também são aceitos.",
                }
                fields = list(dict.fromkeys(str(e["loc"][0]) for e in exc.errors()))
                raise SystemExit(
                    " ".join(
                        messages.get(field, "Confira o cadastro.") for field in fields
                    )
                ) from None
            if db.scalar(select(User).where(User.phone == data.phone)):
                raise SystemExit("Celular já cadastrado.")
            u = User(
                name=data.name,
                phone=data.phone,
                password_hash=hash_password(password),
                roles=data.roles,
            )
            db.add(u)
            db.flush()
            audit(db, u, u.id, "administrator_created")
            db.commit()
            print("Administrador criado.")
        elif args.command == "seed-course":
            for c in CATEGORIES:
                if not db.get(Category, c["code"]):
                    db.add(Category(**c))
            drafts = [
                (
                    "Organize suas informações",
                    "Reúna comprovantes de renda, despesas e dívidas. Deixe em branco os valores desconhecidos.",
                    "rendas",
                    "03 - Componentes do Planejamento Financeiro",
                    "p. 69–71: informações e dados",
                ),
                (
                    "Renda líquida",
                    "Use a renda líquida efetivamente recebida, depois dos descontos.",
                    "rendas",
                    "03 - Componentes do Planejamento Financeiro",
                    "p. 70–71: renda líquida",
                ),
                (
                    "Consignados sem duplicidade",
                    "Indique se o consignado já foi descontado da renda informada para evitar uma segunda subtração.",
                    "consignados",
                    "05 - Como Montar o seu Planejamento Financeiro",
                    "p. 73–75: consignados",
                ),
                (
                    "Custo de vida",
                    "Separe despesas fixas, variáveis e eventuais. Financiamentos com garantia são registrados como despesas apropriadas.",
                    "fixas",
                    "03 - Componentes do Planejamento Financeiro",
                    "p. 70–71: despesas",
                ),
                (
                    "Planeje os próximos meses",
                    "Registre rendas e despesas no mês previsto. Previsão não significa pagamento ou recebimento confirmado.",
                    "eventuais",
                    "05 - Como Montar o seu Planejamento Financeiro",
                    "p. 72–77: visão anual",
                ),
                (
                    "Metas e negociação",
                    "Defina seus objetivos e prazos. Reúna informações das dívidas para conversar com a consultoria, sem presumir descontos.",
                    "metas",
                    "03 - Componentes do Planejamento Financeiro",
                    "p. 69–71: metas e levantamento de dívidas",
                ),
                (
                    "Planejamento em família",
                    "Quando adequado à sua realidade, envolva a família na organização das informações e dos objetivos.",
                    "variaveis",
                    "04 - A importância da Família no seu Planejamento Financeiro",
                    "p. 71–72: abertura",
                ),
            ]
            for title, text, ctx, lesson, ref in drafts:
                if db.scalar(select(Content.id).where(Content.title == title)):
                    continue
                values = dict(
                    title=title,
                    text=text,
                    module="Módulo 02 – Planejamento financeiro",
                    lesson=lesson,
                    reference="Conteudo do curso.pdf, " + ref,
                    context=ctx,
                    status="rascunho",
                    version=1,
                )
                c = Content(**values)
                db.add(c)
                db.flush()
                db.add(ContentVersion(content_id=c.id, version=1, snapshot=values))
            db.commit()
            print("Categorias e rascunhos cadastrados. Nenhum conteúdo foi publicado.")
        else:
            if os.getenv("ALLOW_DEMO") != "1" or os.getenv("APP_ENV") == "production":
                raise SystemExit(
                    "Use somente banco fictício, ALLOW_DEMO=1 e ambiente fora de produção."
                )
            for role, phone, name in [
                ("administrador", "+5511999990001", "Administrador fictício"),
                ("aluno", "+5511999990002", "Maria · conta fictícia"),
                ("aluno", "+5511999990003", "João · conta fictícia"),
                ("consultor", "+5511999990004", "Consultor fictício"),
                ("vendedor", "+5511999990005", "Vendedor fictício"),
            ]:
                if db.scalar(select(User).where(User.phone == phone)):
                    continue
                password = secrets.token_urlsafe(18)
                u = User(
                    name=name,
                    phone=phone,
                    password_hash=hash_password(password),
                    roles=[role],
                    status="ativo" if role == "aluno" else "pendente",
                    released_at=now() if role == "aluno" else None,
                    expires_at=annual(now()) if role == "aluno" else None,
                )
                db.add(u)
                print(f"FICTÍCIO {role}: {phone} / {password}")
            db.commit()


if __name__ == "__main__":
    main()
