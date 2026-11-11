"""Contrat partagé : SQLite, validations et calculs (membre B)."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

STATUSES = ('À faire', 'En cours', 'Terminé')
STRATEGIES = ('Réduire', 'Éviter', 'Transférer', 'Accepter')

def score(probability, impact):
    if any(type(v) is not int or not 1 <= v <= 5 for v in (probability, impact)):
        raise ValueError('Probabilité et impact : entiers de 1 à 5.')
    return probability * impact

def level(value):
    if not 1 <= value <= 25:
        raise ValueError('Score hors limites.')
    return 'Faible' if value <= 4 else 'Modéré' if value <= 9 else 'Élevé' if value <= 16 else 'Critique'

def required(value, label):
    value = str(value).strip()
    if not value or len(value) > 2000:
        raise ValueError(f'{label} : texte requis, maximum 2000 caractères.')
    return value

class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv('SMCA_DB', 'data/smca.db'))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS activities (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL,
              dependencies TEXT NOT NULL, financial INTEGER NOT NULL CHECK(financial BETWEEN 1 AND 5),
              operational INTEGER NOT NULL CHECK(operational BETWEEN 1 AND 5),
              reputation INTEGER NOT NULL CHECK(reputation BETWEEN 1 AND 5),
              rto REAL NOT NULL CHECK(rto > 0), rpo REAL NOT NULL CHECK(rpo >= 0),
              mtpd REAL NOT NULL CHECK(mtpd >= rto));
            CREATE TABLE IF NOT EXISTS risks (
              id INTEGER PRIMARY KEY, activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE RESTRICT,
              title TEXT NOT NULL, asset TEXT NOT NULL, cause TEXT NOT NULL, consequence TEXT NOT NULL,
              owner TEXT NOT NULL, probability INTEGER NOT NULL CHECK(probability BETWEEN 1 AND 5),
              impact INTEGER NOT NULL CHECK(impact BETWEEN 1 AND 5),
              residual_p INTEGER NOT NULL CHECK(residual_p BETWEEN 1 AND 5),
              residual_i INTEGER NOT NULL CHECK(residual_i BETWEEN 1 AND 5));
            CREATE TABLE IF NOT EXISTS treatments (
              id INTEGER PRIMARY KEY, risk_id INTEGER NOT NULL REFERENCES risks(id) ON DELETE RESTRICT,
              action TEXT NOT NULL, strategy TEXT NOT NULL, owner TEXT NOT NULL, due TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('À faire','En cours','Terminé')), evidence TEXT NOT NULL);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def rows(self, table):
        if table not in ('activities', 'risks', 'treatments'):
            raise ValueError('Table inconnue.')
        with self.connection() as db:
            rows = [dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY id')]
        for row in rows:
            if table == 'activities':
                row['criticality'] = max(row[k] for k in ('financial','operational','reputation'))
                row['priority'] = 'Prioritaire' if row['criticality'] >= 4 or row['rto'] <= 4 else 'Standard'
            if table == 'risks':
                row['score'] = score(row['probability'], row['impact'])
                row['level'] = level(row['score'])
                row['residual_score'] = score(row['residual_p'], row['residual_i'])
                row['residual_level'] = level(row['residual_score'])
            if table == 'treatments':
                row['overdue'] = row['status'] != 'Terminé' and date.fromisoformat(row['due']) < date.today()
        return rows

    def _save(self, table, values, item_id=None):
        with self.connection() as db:
            if item_id is None:
                marks = ','.join('?' for _ in values)
                return db.execute(f"INSERT INTO {table} ({','.join(values)}) VALUES ({marks})", tuple(values.values())).lastrowid
            cursor = db.execute(f"UPDATE {table} SET {','.join(k+'=?' for k in values)} WHERE id=?", (*values.values(), item_id))
            if not cursor.rowcount:
                raise ValueError('Enregistrement introuvable.')
            return item_id

    def save_activity(self, *, name, owner, dependencies, financial, operational, reputation, rto, rpo, mtpd, item_id=None):
        for v in (financial, operational, reputation):
            score(v, 1)
        import math
        if not all(math.isfinite(v) for v in (rto, rpo, mtpd)) or not (0 < rto <= mtpd and rpo >= 0):
            raise ValueError('BIA : 0 < RTO ≤ MTPD et RPO ≥ 0 ; valeurs finies en heures.')
        return self._save('activities', dict(name=required(name,'Activité'), owner=required(owner,'Responsable'), dependencies=required(dependencies,'Dépendances'), financial=financial, operational=operational, reputation=reputation, rto=rto, rpo=rpo, mtpd=mtpd), item_id)

    def save_risk(self, *, activity_id, title, asset, cause, consequence, owner, probability, impact, residual_p, residual_i, item_id=None):
        score(probability, impact)
        score(residual_p, residual_i)
        return self._save('risks', dict(activity_id=activity_id, title=required(title,'Risque'), asset=required(asset,'Actif'), cause=required(cause,'Cause'), consequence=required(consequence,'Conséquence'), owner=required(owner,'Responsable'), probability=probability, impact=impact, residual_p=residual_p, residual_i=residual_i), item_id)

    def save_treatment(self, *, risk_id, action, strategy, owner, due, status, evidence='', item_id=None):
        date.fromisoformat(str(due))
        if status not in STATUSES or strategy not in STRATEGIES:
            raise ValueError('Statut ou stratégie invalide.')
        if status == 'Terminé' and not evidence.strip():
            raise ValueError('Une preuve est requise pour terminer le traitement.')
        return self._save('treatments', dict(risk_id=risk_id, action=required(action,'Action'), strategy=strategy, owner=required(owner,'Responsable'), due=str(due), status=status, evidence=evidence.strip()), item_id)

    def delete(self, table, item_id):
        if table not in ('activities', 'risks', 'treatments'):
            raise ValueError('Table inconnue.')
        with self.connection() as db:
            db.execute(f'DELETE FROM {table} WHERE id=?', (item_id,))

    def seed(self):
        if any(self.rows(t) for t in ('activities','risks','treatments')):
            raise ValueError('La démonstration nécessite une base vide.')
        a = self.save_activity(name='Prise de commandes', owner='Responsable commercial', dependencies='ERP, base clients, réseau, équipe commerciale', financial=5, operational=4, reputation=4, rto=4., rpo=1., mtpd=24.)
        b = self.save_activity(name='Préparation des livraisons', owner='Responsable logistique', dependencies='Entrepôt, stocks, transporteurs', financial=3, operational=4, reputation=3, rto=8., rpo=4., mtpd=48.)
        for aid, title, asset, p, i, rp, ri in [(a,'Indisponibilité ERP','Serveur ERP',4,5,2,4),(a,'Perte des commandes','Base de données',3,5,1,4),(b,'Coupure électrique','Entrepôt',3,4,2,3),(b,'Absence de personnel','Équipe logistique',2,3,1,3),(a,'Panne du poste de secours','PC de secours',1,2,1,2)]:
            rid = self.save_risk(activity_id=aid,title=title,asset=asset,cause='Défaillance ou indisponibilité de la ressource',consequence='Interruption de l’activité',owner='Responsable informatique' if aid==a else 'Responsable logistique', probability=p,impact=i,residual_p=rp,residual_i=ri)
            self.save_treatment(risk_id=rid,action='Prévoir une solution de secours et tester la reprise',strategy='Réduire',owner='Pilote continuité',due='2026-11-30',status='À faire')

    def backup(self, destination):
        with self.connection() as source, sqlite3.connect(destination) as target:
            source.backup(target)
