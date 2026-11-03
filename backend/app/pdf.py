import io,os
from pathlib import Path
from decimal import Decimal
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing,Rect,String,Line
from .finance import LABELS
from .security import now

def brl(v):return 'Não informado' if v is None else 'R$ '+f'{Decimal(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def generate(student,report,details,notes):
    buf=io.BytesIO();story=[];styles=getSampleStyleSheet()
    def text(s,style='BodyText'):story.extend([Paragraph(escape(str(s)),styles[style]),Spacer(1,8)])
    logo=Path(os.getenv('LOGO_PATH',str(Path(__file__).resolve().parents[2]/'frontend/public/logo.png')))
    if logo.is_file():
        from PIL import Image as PI
        with PI.open(logo) as im:w,h=im.size
        story.append(Image(str(logo),width=250,height=250*h/w))
    text('P4 Consultores · Planejamento financeiro','Title');text(student.name,'Heading2')
    text('Gerado em '+now().astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')+' (Brasília)')
    text('Valores '+('previstos' if report['mode']=='forecast' else 'realizados'))
    if report['incomplete']:text('PREENCHIMENTO INCOMPLETO: os totais são parciais, sem diagnóstico definitivo.')
    rows=[['Mês','Entradas','Saídas consideradas','Sobra ou falta']]+[[r['month'],brl(r['income']),brl(r['outflow']),brl(r['balance'])] for r in report['months']]
    table=Table(rows,repeatRows=1,colWidths=[65,130,140,140]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#124a57')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf3f2')]),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]));story.append(table)
    text('Totais anuais: entradas '+brl(report['totals']['income'])+'; saídas '+brl(report['totals']['outflow'])+'; diferença '+brl(report['totals']['balance']))
    text('Entradas e saídas mensais','Heading2');d=Drawing(475,170);maximum=max([float(r['income'] or 0) for r in report['months']]+[float(r['outflow']) for r in report['months']]+[1])
    for i,r in enumerate(report['months']):
        for j,k in enumerate(['income','outflow']):d.add(Rect(i*39+j*12+5,20,10,float(r[k] or 0)/maximum*120,fillColor=colors.HexColor('#124a57' if j==0 else '#b18a58'),strokeColor=None))
        d.add(String(i*39+4,5,r['month'][5:],fontSize=8))
    d.add(String(5,155,'Azul: entradas. Dourado: saídas. Valores na tabela.',fontSize=9));story.append(d)
    text('Sobra ou falta ao longo dos meses','Heading2');d=Drawing(475,150);d.add(Line(0,70,475,70,strokeColor=colors.grey));maximum=max([abs(float(r['balance'] or 0)) for r in report['months']]+[1])
    for i,r in enumerate(report['months']):
        v=float(r['balance'] or 0)/maximum*55;d.add(Rect(i*39+5,min(70,70+v),18,abs(v),fillColor=colors.HexColor('#124a57'),strokeColor=None));d.add(String(i*39+4,4,r['month'][5:],fontSize=8))
    story.append(d)
    for r in report['months']:
        text('Categorias e comprometimento · '+r['month'],'Heading2')
        maximum=max([float(v) for c,v in r['categories'].items() if c!='rendas']+[1]);d=Drawing(475,110)
        for i,c in enumerate(c for c in LABELS if c!='rendas'):
            pct=r['percentages'][c];text(LABELS[c]+': '+brl(r['categories'][c])+' | '+(pct+'% da renda' if pct is not None else 'Percentual indisponível: renda zero ou ausente.'))
            d.add(String(0,95-i*18,LABELS[c][:27],fontSize=8));d.add(Rect(165,93-i*18,float(r['categories'][c])/maximum*270,9,fillColor=colors.HexColor('#124a57'),strokeColor=None))
        story.append(d);text('Comprometimento da renda (%)','Heading3');d=Drawing(475,110);maximum=max([float(v or 0) for v in r['percentages'].values()]+[100])
        if all(v is None for v in r['percentages'].values()):text('Gráfico percentual indisponível: renda zero ou ausente.')
        else:
            for i,(c,v) in enumerate(r['percentages'].items()):
                d.add(String(0,95-i*18,LABELS[c][:27],fontSize=8));d.add(Rect(165,93-i*18,float(v or 0)/maximum*225,9,fillColor=colors.HexColor('#b18a58'),strokeColor=None));d.add(String(400,95-i*18,str(v or 0)+'%',fontSize=8))
            story.append(d)
    text('Categorias de acompanhamento podem conter valores excluídos das saídas. Não some os percentuais como composição do orçamento.')
    text('Dívidas cadastradas','Heading2')
    for x in details['debts']:text(f"{x['institution']} · {x['kind']} · Saldo: {brl(x['balance'])}; parcelas: {x['installments'] if x['installments'] is not None else 'não informado'}; término: {x['end'] or 'não informado'}; garantia: {'sim' if x['guaranteed'] else 'não'}; situação: {x['status']}. {x['notes']}")
    text('Metas e negociação','Heading2')
    for x in details['goals']:text(f"{x['title']} · {brl(x['amount'])} · prazo {x['deadline'] or 'não informado'}. {x['negotiation']}")
    text('Orientações liberadas','Heading2')
    for x in notes:text(x.text)
    text('Modo do cartão: '+report['card_mode']+'. Consignados já descontados não são subtraídos novamente. Saldo devedor não é saída mensal.')
    SimpleDocTemplate(buf,pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=35).build(story);buf.seek(0);return buf
