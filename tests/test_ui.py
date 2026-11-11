from pathlib import Path
from streamlit.testing.v1 import AppTest
from smca.service import Store

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_empty_and_demo_navigation(tmp_path,monkeypatch):
    monkeypatch.setenv('SMCA_DB',str(tmp_path/'ui.db'))
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    assert not at.exception
    assert at.metric[1].value=='0'
    at.sidebar.button[0].click().run()
    assert at.metric[1].value=='5'
    for page in ['Activités / BIA','Registre des risques','Plans de traitement','Exports & méthode','Tableau de bord']:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception

def test_create_activity_and_validation(tmp_path,monkeypatch):
    path=tmp_path/'form.db'; monkeypatch.setenv('SMCA_DB',str(path))
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    at.sidebar.radio[0].set_value('Activités / BIA').run()
    at.button[0].click().run()
    assert at.error
    at.text_input[0].set_value('Facturation')
    at.text_input[1].set_value('Membre A')
    at.text_area[0].set_value('ERP et équipe comptable')
    at.button[0].click().run()
    assert not at.exception
    assert Store(path).rows('activities')[0]['name']=='Facturation'

def test_risk_and_treatment_workflow(tmp_path,monkeypatch):
    path=tmp_path/'workflow.db'; monkeypatch.setenv('SMCA_DB',str(path))
    store=Store(path); store.seed()
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    at.sidebar.radio[0].set_value('Registre des risques').run()
    for label,value in [('Risque','Panne réseau'),('Actif concerné','Routeur'),('Responsable du risque','Membre B')]:
        next(w for w in at.text_input if w.label==label).set_value(value)
    for label,value in [('Cause','Défaillance matérielle'),('Conséquence','Commandes interrompues')]:
        next(w for w in at.text_area if w.label==label).set_value(value)
    next(w for w in at.button if w.label=='Enregistrer le risque').click().run()
    assert not at.exception
    risk=store.rows('risks')[-1]
    assert risk['title']=='Panne réseau' and risk['score']==9
    at.sidebar.radio[0].set_value('Plans de traitement').run()
    next(w for w in at.selectbox if w.label=='Risque lié').set_value(risk['id'])
    next(w for w in at.text_area if w.label=='Action de traitement').set_value('Installer un routeur de secours')
    next(w for w in at.text_input if w.label=='Pilote').set_value('Membre B')
    next(w for w in at.selectbox if w.label=='Statut').set_value('Terminé')
    next(w for w in at.button if w.label=='Enregistrer le traitement').click().run()
    assert at.error
    next(w for w in at.text_area if w.label=='Preuve / résultat du test').set_value('Bascule testée en 10 minutes')
    next(w for w in at.button if w.label=='Enregistrer le traitement').click().run()
    assert not at.exception
    assert store.rows('treatments')[-1]['status']=='Terminé'
    assert store.rows('treatments')[-1]['risk_id']==risk['id']
