from decimal import Decimal,InvalidOperation
from datetime import date
import json
from pathlib import Path
CATEGORIES=json.loads(Path(__file__).with_name('categories.json').read_text())
CODES=[c['code'] for c in CATEGORIES]
LABELS={c['code']:c['label'] for c in CATEGORIES}
def money(v):
    if v is None or v=='':return None
    try:
        d=Decimal(str(v))
        if not d.is_finite() or d<0 or d>Decimal('999999999999.99') or d.as_tuple().exponent < -2:raise ValueError()
        return d.quantize(Decimal('.01'))
    except (InvalidOperation,ValueError):raise ValueError('Use um valor positivo com até duas casas decimais ou deixe em branco.')
def months(start):
    d=date.fromisoformat(start+'-01');n=d.year*12+d.month-1
    return [f'{(n+i)//12:04d}-{(n+i)%12+1:02d}' for i in range(12)]
def calculate(plan,entries,mode='forecast'):
    result=[]
    for month in months(plan.start):
        totals={c:Decimal(0) for c in CODES};out=Decimal(0);known=False;missing=0
        for e in entries:
            if e.month!=month:continue
            v=Decimal(0) if e.absent else getattr(e,mode)
            if v is None:missing+=1;continue
            totals[e.category]+=v
            if e.category=='rendas':known=True
            elif not ((e.category=='consignados' and e.deducted) or (plan.card_mode=='categorias' and e.method=='fatura') or (plan.card_mode=='fatura' and e.method=='cartao')):out+=v
        income=totals['rendas'] if known else None
        result.append({'month':month,'income':str(income) if income is not None else None,'outflow':str(out),'balance':str(income-out) if income is not None else None,'categories':{c:str(v) for c,v in totals.items()},'percentages':{c:str((v/income*100).quantize(Decimal('.01'))) if income is not None and income>0 else None for c,v in totals.items() if c!='rendas'},'missing':missing,'incomplete':missing>0 or not known or len(plan.completed)<8})
    income=sum((Decimal(r['income']) for r in result if r['income'] is not None),Decimal(0));out=sum((Decimal(r['outflow']) for r in result),Decimal(0))
    return {'mode':mode,'months':result,'totals':{'income':str(income) if any(r['income'] is not None for r in result) else None,'outflow':str(out),'balance':str(income-out) if all(r['income'] is not None for r in result) else None},'incomplete':any(r['incomplete'] for r in result),'card_mode':plan.card_mode}
