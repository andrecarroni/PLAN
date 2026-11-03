from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .models import Plan,Entry,Debt,Goal
from .security import now
from zoneinfo import ZoneInfo
EF=['key','category','label','month','forecast','actual','deducted','method','absent']
DF=['key','institution','kind','balance','installments','end','guaranteed','status','notes']
GF=['title','amount','deadline','negotiation']
def serial(obj,fields):return {k:str(getattr(obj,k)) if isinstance(getattr(obj,k),Decimal) else getattr(obj,k) for k in fields}
def get_plan(db,sid):
    p=db.scalar(select(Plan).where(Plan.user_id==sid))
    if not p:
        start=now().astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%Y-%m')
        p=Plan(user_id=sid,start=start,selected_month=start,version=1,step=0,completed=[],card_mode='categorias');db.add(p)
        try:db.commit()
        except IntegrityError:db.rollback();p=db.scalar(select(Plan).where(Plan.user_id==sid))
    return p
def payload(db,p):
    return {'id':p.id,'user_id':p.user_id,'version':p.version,'start':p.start,'selected_month':p.selected_month,'step':p.step,'completed':p.completed,'card_mode':p.card_mode,'entries':[serial(x,EF) for x in db.scalars(select(Entry).where(Entry.plan_id==p.id))],'debts':[serial(x,DF) for x in db.scalars(select(Debt).where(Debt.plan_id==p.id))],'goals':[serial(x,GF) for x in db.scalars(select(Goal).where(Goal.plan_id==p.id))]}
