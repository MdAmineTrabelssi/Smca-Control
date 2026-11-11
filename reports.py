"""Exports et présentation des données (membre A)."""
import csv
import io
from datetime import datetime
from html import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

def csv_bytes(rows):
    out = io.StringIO(newline='')
    if rows:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        for row in rows:
            safe = {k: ("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v) for k,v in row.items()}
            writer.writerow(safe)
    return out.getvalue().encode('utf-8-sig')

def pdf_bytes(store):
    out = io.BytesIO()
    styles = getSampleStyleSheet()
    def p(text, style='BodyText'):
        return Paragraph(escape(str(text)).replace('\n','<br/>'), styles[style])
    story = [p('SMCA | Rapport de continuité', 'Title'), p('Mini-projet N°6 • '+datetime.now().strftime('%d/%m/%Y %H:%M')), Spacer(1,12), p('Méthode : score = probabilité × impact. Faible 1-4, modéré 5-9, élevé 10-16, critique 17-25. Les scores résiduels sont des estimations à confirmer par des tests de reprise.'), Spacer(1,12)]
    risks = store.rows('risks')
    story.append(p('Matrice initiale 5 × 5', 'Heading2'))
    matrix = [[p('P / I')] + [p(i) for i in range(1,6)]]
    for prob in range(5,0,-1):
        matrix.append([p(prob)] + [p(f'{prob*imp} | {sum(r["probability"]==prob and r["impact"]==imp for r in risks)} risque(s)') for imp in range(1,6)])
    table = Table(matrix, colWidths=[40]+[91]*5)
    commands=[('GRID',(0,0),(-1,-1),.5,colors.white),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]
    for y, prob in enumerate(range(5,0,-1),1):
        for imp in range(1,6):
            s=prob*imp
            commands.append(('BACKGROUND',(imp,y),(imp,y),colors.HexColor('#d1fae5' if s<=4 else '#fef3c7' if s<=9 else '#fed7aa' if s<=16 else '#fecaca')))
    table.setStyle(TableStyle(commands))
    story.extend([table, Spacer(1,16)])
    sections = [('activities','Activités et BIA'),('risks','Registre des risques'),('treatments','Plans de traitement')]
    for key, title in sections:
        if key != 'activities':
            story.append(PageBreak())
        story.append(p(title,'Heading1'))
        rows=store.rows(key)
        if not rows:
            story.append(p('Aucun enregistrement.'))
        for row in rows:
            if key=='activities':
                title=f'A{row["id"]} - {row["name"]}'
                text=f'Responsable : {row["owner"]}\nDépendances : {row["dependencies"]}\nImpacts financier / opérationnel / réputation : {row["financial"]} / {row["operational"]} / {row["reputation"]}\nRTO : {row["rto"]} h ; RPO : {row["rpo"]} h ; MTPD : {row["mtpd"]} h\nPriorité : {row["priority"]}'
            elif key=='risks':
                title=f'R{row["id"]} - {row["title"]}'
                text=f'Activité A{row["activity_id"]} | Actif : {row["asset"]} | Responsable : {row["owner"]}\nCause : {row["cause"]}\nConséquence : {row["consequence"]}\nInitial : {row["probability"]} × {row["impact"]} = {row["score"]} ({row["level"]})\nRésiduel estimé : {row["residual_p"]} × {row["residual_i"]} = {row["residual_score"]} ({row["residual_level"]})'
            else:
                title=f'T{row["id"]} - Risque R{row["risk_id"]}'
                text=f'{row["strategy"]} : {row["action"]}\nPilote : {row["owner"]} | Échéance : {row["due"]} | {row["status"]}\nEn retard : {"oui" if row["overdue"] else "non"}\nPreuve : {row["evidence"] or "Non renseignée"}'
            story.append(KeepTogether([p(title,'Heading3'),p(text),Spacer(1,8)]))
    def footer(canvas, doc):
        canvas.setFont('Helvetica',8)
        canvas.drawString(42,24,'SMCA - Document pédagogique - Données déclaratives')
        canvas.drawRightString(A4[0]-42,24,str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
