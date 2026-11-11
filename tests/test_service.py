import csv
import io
import sqlite3
import pytest
from pypdf import PdfReader
from smca.service import Store, score, level
from smca.reports import csv_bytes, pdf_bytes

@pytest.fixture
def store(tmp_path):
    s=Store(tmp_path/'test.db')
    s.seed()
    return s

@pytest.mark.parametrize('p',range(1,6))
@pytest.mark.parametrize('i',range(1,6))
def test_all_matrix_scores(p,i):
    assert score(p,i)==p*i

@pytest.mark.parametrize('s,label',[(1,'Faible'),(4,'Faible'),(5,'Modéré'),(9,'Modéré'),(10,'Élevé'),(16,'Élevé'),(17,'Critique'),(25,'Critique')])
def test_thresholds(s,label):
    assert level(s)==label

@pytest.mark.parametrize('p,i',[(0,1),(6,1),(1,-1),(1,6),(1.5,2),(True,1)])
def test_invalid_score(p,i):
    with pytest.raises(ValueError): score(p,i)

def test_persistence_update_delete_backup(store,tmp_path):
    risk=store.rows('risks')[0]
    for key in ('score','level','residual_score','residual_level'): risk.pop(key)
    rid=risk.pop('id'); risk['title']='Risque modifié'; risk['probability']=5
    store.save_risk(item_id=rid,**risk)
    assert Store(store.path).rows('risks')[0]['score']==25
    with pytest.raises(sqlite3.IntegrityError): store.delete('activities',1)
    with pytest.raises(sqlite3.IntegrityError): store.delete('risks',rid)
    store.delete('treatments',1); store.delete('risks',rid)
    assert len(store.rows('risks'))==4
    destination=tmp_path/'backup.db'; store.backup(destination)
    assert Store(destination).rows('risks')==store.rows('risks')

def test_bia_validation(store):
    a=store.rows('activities')[0]
    assert a['priority']=='Prioritaire'
    for k in ('id','criticality','priority'): a.pop(k)
    for changes in ({'rto':25.},{'rpo':-1.},{'rto':0.},{'mtpd':float('nan')},{'name':'  '}):
        with pytest.raises(ValueError): store.save_activity(**(a|changes))

def test_treatment_validation_and_lateness(store):
    args=dict(risk_id=1,action='Restaurer la sauvegarde',strategy='Réduire',owner='B',due='2000-01-01',status='Terminé')
    with pytest.raises(ValueError): store.save_treatment(**args)
    tid=store.save_treatment(**(args|{'status':'En cours'}))
    assert store.rows('treatments')[-1]['overdue']
    store.save_treatment(item_id=tid,**args,evidence='Restauration en 2 heures')
    assert not store.rows('treatments')[-1]['overdue']
    with pytest.raises(sqlite3.IntegrityError): store.save_treatment(**(args|{'risk_id':999,'evidence':'OK'}))

def test_duplicate_seed_refused(store):
    with pytest.raises(ValueError): store.seed()
    assert len(store.rows('risks'))==5

def test_csv_roundtrip_and_formula_protection():
    rows=[dict(title='Électricité; "serveur"\nTest',owner='=SUM(A1:A2)')]
    result=list(csv.DictReader(io.StringIO(csv_bytes(rows).decode('utf-8-sig')),delimiter=';'))
    assert result[0]['title']==rows[0]['title']
    assert result[0]['owner'].startswith("'=")

def test_pdf_content_and_empty_database(store,tmp_path):
    for source in (store,Store(tmp_path/'empty.db')):
        data=pdf_bytes(source)
        reader=PdfReader(io.BytesIO(data))
        text='\n'.join(page.extract_text() for page in reader.pages)
        assert 'Matrice initiale' in text and 'Plans de traitement' in text
        if source is store: assert 'Indisponibilité ERP' in text

def test_pdf_long_escaped_text(store):
    r=store.rows('risks')[0]
    for k in ('id','score','level','residual_score','residual_level'): r.pop(k)
    r['title']='<script> & panne'; r['cause']='Longue description détaillée. '*60
    store.save_risk(**r)
    assert len(PdfReader(io.BytesIO(pdf_bytes(store))).pages)>=2
