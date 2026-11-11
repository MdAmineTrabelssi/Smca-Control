"""Interface Streamlit : membre A. Exécuter : streamlit run app.py."""
from datetime import date
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from smca.service import Store, STATUSES, STRATEGIES
from smca.reports import csv_bytes, pdf_bytes

st.set_page_config(page_title='SMCA Control', page_icon='🛡️', layout='wide')
st.markdown(f'<style>{(Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)
store = Store()
st.sidebar.markdown('''<div class="brand"><div class="brand-mark">◈</div><div>
<div class="brand-name">SMCA Control</div><div class="brand-sub">Continuité & maîtrise des risques</div>
</div></div>''', unsafe_allow_html=True)
st.sidebar.caption('MINI-PROJET N°6 · BINÔME A + B')
page = st.sidebar.radio('Navigation', ['Tableau de bord','Activités / BIA','Registre des risques','Plans de traitement','Exports & méthode'])
if st.sidebar.button('Charger la démonstration'):
    try:
        store.seed()
        st.sidebar.success('Données chargées.')
    except ValueError as exc:
        st.sidebar.warning(str(exc))
st.sidebar.markdown('---')
st.sidebar.caption('🔒 Application locale · Données SQLite persistantes')

PAGE_META = {
    'Tableau de bord': ('Vue d’ensemble', 'Pilotez la continuité en un coup d’œil', 'Identifiez les interruptions prioritaires et suivez les actions de réduction.'),
    'Activités / BIA': ('Analyse d’impact', 'Cartographiez les activités critiques', 'Définissez les dépendances, les impacts et les objectifs de reprise.'),
    'Registre des risques': ('Évaluation', 'Centralisez les risques de continuité', 'Reliez chaque scénario à une activité, un actif et un responsable.'),
    'Plans de traitement': ('Suivi des actions', 'Transformez les risques en décisions', 'Pilotez les mesures, les échéances et les preuves de réalisation.'),
    'Exports & méthode': ('Rapports', 'Partagez une vision claire et vérifiable', 'Exportez les registres et retrouvez les conventions de calcul.'),
}
kicker, title, subtitle = PAGE_META[page]
st.markdown(f'''<section class="page-hero"><div class="page-kicker">{kicker}</div>
<h1>{title}</h1><p>{subtitle}</p></section>''', unsafe_allow_html=True)
if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))

def save(function, **kwargs):
    try:
        function(**kwargs)
        st.session_state.notice = 'Enregistrement sauvegardé.'
        st.rerun()
    except (ValueError, sqlite3.IntegrityError) as exc:
        st.error(f'Saisie non enregistrée : {exc}')

def editor(table, label):
    rows = store.rows(table)
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info('Aucune donnée. Ajoutez un enregistrement ou chargez la démonstration.')
    options = {r['id']:r for r in rows}
    selected = st.selectbox('Créer ou modifier', [None]+list(options), format_func=lambda x:'Nouvel enregistrement' if x is None else f'#{x} - {options[x][label]}')
    return selected, options.get(selected,{})

def deletion(table, item_id):
    if item_id is not None:
        with st.expander('Supprimer cet enregistrement'):
            confirmed = st.checkbox('Je confirme la suppression')
            if st.button('Supprimer', disabled=not confirmed):
                try:
                    store.delete(table,item_id)
                    st.session_state.notice='Enregistrement supprimé.'
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error('Suppression impossible : supprimez d’abord les risques ou traitements liés.')

def matrix(risks, residual=False):
    pk, ik = ('residual_p','residual_i') if residual else ('probability','impact')
    z = [[0 if p*i<=4 else 1 if p*i<=9 else 2 if p*i<=16 else 3 for i in range(1,6)] for p in range(1,6)]
    texts = [[f'{p*i}<br>{sum(r[pk]==p and r[ik]==i for r in risks)} risque(s)' for i in range(1,6)] for p in range(1,6)]
    fig=go.Figure(go.Heatmap(z=z,x=list(range(1,6)),y=list(range(1,6)),text=texts,texttemplate='%{text}',zmin=0,zmax=3,showscale=False,colorscale=[[0,'#2dd4a7'],[.1666,'#2dd4a7'],[.1667,'#f3cd5b'],[.5,'#f3cd5b'],[.5001,'#f19753'],[.8333,'#f19753'],[.8334,'#ef6378'],[1,'#ef6378']],xgap=6,ygap=6,hovertemplate='<b>Impact %{x} · Probabilité %{y}</b><br>%{text}<extra></extra>'))
    fig.update_traces(textfont=dict(color='#07111f',size=12))
    fig.update_layout(height=470,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#b8c4d6'),xaxis=dict(title='Impact',dtick=1,gridcolor='rgba(148,163,184,.08)',fixedrange=True),yaxis=dict(title='Probabilité',dtick=1,gridcolor='rgba(148,163,184,.08)',fixedrange=True),margin=dict(l=35,r=10,t=12,b=30))
    return fig

if page == 'Tableau de bord':
    risks=store.rows('risks'); activities=store.rows('activities'); plans=store.rows('treatments')
    cols=st.columns(4)
    for col,label,val in zip(cols,['Activités','Risques','Risques critiques','Actions en retard'],[len(activities),len(risks),sum(r['score']>=17 for r in risks),sum(t['overdue'] for t in plans)]):
        col.metric(label,val)
    st.markdown('<div class="section-label">Cartographie des risques</div>', unsafe_allow_html=True)
    residual=st.toggle('Afficher le risque résiduel estimé')
    st.plotly_chart(matrix(risks,residual),use_container_width=True,config={'displayModeBar':False})
    st.markdown('''<div class="legend-row">
    <span class="legend-chip legend-low">Faible · 1–4</span>
    <span class="legend-chip legend-medium">Modéré · 5–9</span>
    <span class="legend-chip legend-high">Élevé · 10–16</span>
    <span class="legend-chip legend-critical">Critique · 17–25</span></div>''', unsafe_allow_html=True)
    if risks:
        st.subheader('Risques à traiter en priorité')
        st.dataframe(pd.DataFrame(sorted(risks,key=lambda r:r['score'],reverse=True))[['id','title','owner','score','level','residual_score']],hide_index=True,use_container_width=True)
    else:
        st.info('Commencez par une activité dans « Activités / BIA », ou chargez la démonstration dans le menu.')

elif page == 'Activités / BIA':
    st.caption('BIA : analyse des impacts d’une interruption. Toutes les durées sont en heures.')
    item_id,r=editor('activities','name')
    with st.form(f'activity-{item_id}'):
        name=st.text_input('Activité',r.get('name',''))
        owner=st.text_input('Responsable',r.get('owner',''))
        dependencies=st.text_area('Ressources et dépendances',r.get('dependencies',''))
        cols=st.columns(3)
        vals=[col.number_input(label,1,5,int(r.get(key,3))) for col,label,key in zip(cols,['Impact financier','Impact opérationnel','Impact réputation'],['financial','operational','reputation'])]
        cols=st.columns(3)
        rto=cols[0].number_input('RTO : délai cible de reprise (h)',min_value=0.25,value=float(r.get('rto',4)),step=.25)
        rpo=cols[1].number_input('RPO : perte de données tolérée (h)',min_value=0.,value=float(r.get('rpo',1)),step=.25)
        mtpd=cols[2].number_input('MTPD : interruption maximale tolérée (h)',min_value=.25,value=float(r.get('mtpd',24)),step=.25)
        if st.form_submit_button('Enregistrer l’activité'):
            save(store.save_activity,item_id=item_id,name=name,owner=owner,dependencies=dependencies,financial=vals[0],operational=vals[1],reputation=vals[2],rto=rto,rpo=rpo,mtpd=mtpd)
    deletion('activities',item_id)

elif page == 'Registre des risques':
    risks=store.rows('risks')
    search=st.text_input('Rechercher un risque')
    selected_level=st.selectbox('Filtrer le niveau',['Tous','Faible','Modéré','Élevé','Critique'])
    if search or selected_level!='Tous':
        filtered=[r for r in risks if search.casefold() in (r['title']+' '+r['asset']+' '+r['owner']).casefold() and (selected_level=='Tous' or r['level']==selected_level)]
        st.write(f'{len(filtered)} résultat(s)')
        st.dataframe(pd.DataFrame(filtered),use_container_width=True)
    activities={a['id']:a['name'] for a in store.rows('activities')}
    if not activities:
        st.info('Créez d’abord une activité dans « Activités / BIA ».')
    else:
        item_id,r=editor('risks','title')
        with st.form(f'risk-{item_id}'):
            ids=list(activities)
            aid=st.selectbox('Activité liée',ids,index=ids.index(r['activity_id']) if r else 0,format_func=lambda x:activities[x])
            title=st.text_input('Risque',r.get('title',''))
            asset=st.text_input('Actif concerné',r.get('asset',''))
            cause=st.text_area('Cause',r.get('cause',''))
            consequence=st.text_area('Conséquence',r.get('consequence',''))
            owner=st.text_input('Responsable du risque',r.get('owner',''))
            cols=st.columns(4)
            vals=[col.number_input(label,1,5,int(r.get(key,3))) for col,label,key in zip(cols,['Probabilité initiale','Impact initial','Probabilité résiduelle estimée','Impact résiduel estimé'],['probability','impact','residual_p','residual_i'])]
            st.caption('Le résiduel est une estimation après traitement, à confirmer par un exercice.')
            if st.form_submit_button('Enregistrer le risque'):
                save(store.save_risk,item_id=item_id,activity_id=aid,title=title,asset=asset,cause=cause,consequence=consequence,owner=owner,probability=vals[0],impact=vals[1],residual_p=vals[2],residual_i=vals[3])
        deletion('risks',item_id)

elif page == 'Plans de traitement':
    risks={r['id']:r['title'] for r in store.rows('risks')}
    if not risks:
        st.info('Créez d’abord un risque.')
    else:
        item_id,r=editor('treatments','action')
        with st.form(f'treatment-{item_id}'):
            ids=list(risks)
            rid=st.selectbox('Risque lié',ids,index=ids.index(r['risk_id']) if r else 0,format_func=lambda x:risks[x])
            action=st.text_area('Action de traitement',r.get('action',''))
            strategy=st.selectbox('Stratégie',STRATEGIES,index=STRATEGIES.index(r.get('strategy',STRATEGIES[0])))
            owner=st.text_input('Pilote',r.get('owner',''))
            due=st.date_input('Échéance',date.fromisoformat(r['due']) if r else date.today())
            status=st.selectbox('Statut',STATUSES,index=STATUSES.index(r.get('status',STATUSES[0])))
            evidence=st.text_area('Preuve / résultat du test',r.get('evidence',''))
            if st.form_submit_button('Enregistrer le traitement'):
                save(store.save_treatment,item_id=item_id,risk_id=rid,action=action,strategy=strategy,owner=owner,due=due.isoformat(),status=status,evidence=evidence)
        deletion('treatments',item_id)

else:
    st.subheader('Télécharger les données')
    for table,label in [('activities','Activités BIA'),('risks','Registre des risques'),('treatments','Plans de traitement')]:
        rows=store.rows(table)
        st.download_button(f'CSV · {label}',csv_bytes(rows),file_name=f'smca_{table}.csv',mime='text/csv',disabled=not rows)
    st.download_button('Rapport PDF complet',pdf_bytes(store),file_name='rapport_smca.pdf',mime='application/pdf')
    st.subheader('Convention d’évaluation')
    st.markdown('''Probabilité : **1 rare · 2 peu probable · 3 possible · 4 probable · 5 très probable**.

Impact : **1 mineur · 2 limité · 3 significatif · 4 majeur · 5 catastrophique**.

Score = probabilité × impact. **Faible 1–4 / Modéré 5–9 / Élevé 10–16 / Critique 17–25**.

BIA : criticité = maximum des trois impacts. Activité prioritaire si criticité ≥ 4 ou RTO ≤ 4 h.
RTO ≤ MTPD ; le RPO décrit une perte de données, distincte du délai de reprise.

Ces seuils sont des conventions pédagogiques à valider avec l’enseignant et les responsables métier.
L’application ne constitue pas une certification ISO 22301 ni un plan de continuité complet.''')
