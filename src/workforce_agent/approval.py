"""Transactional demo calendar, immutable proposal snapshots, and durable audit.

This adapter updates only an isolated demo calendar, never Google Calendar.
"""
import json
import secrets
import sqlite3
from copy import deepcopy
from pathlib import Path


class ApprovalStore:
    def __init__(self, path=':memory:'):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS demo_events (session TEXT, id TEXT, version INTEGER, data TEXT, PRIMARY KEY(session,id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS proposals (session TEXT, id TEXT, data TEXT, PRIMARY KEY(session,id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS approval_audit (id INTEGER PRIMARY KEY, session TEXT, proposal TEXT, data TEXT)')
        self.db.commit()

    def seed(self, sid, activities):
        with self.db:
            for a in activities:
                self.db.execute('INSERT INTO demo_events VALUES (?,?,?,?)', (sid,a['id'],1,json.dumps(a)))

    def events(self, sid):
        return [{**json.loads(data), 'version':version} for data,version in self.db.execute('SELECT data,version FROM demo_events WHERE session=? ORDER BY id', (sid,))]

    def proposals(self, sid):
        return [json.loads(row[0]) for row in self.db.execute('SELECT data FROM proposals WHERE session=? ORDER BY rowid', (sid,))]

    def get(self, sid, pid):
        row = self.db.execute('SELECT data FROM proposals WHERE session=? AND id=?', (sid,pid)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, sid, suggestions, activities, actor, timestamp):
        saved = []
        with self.db:
            for previous in self.proposals(sid):
                if previous['approval'] == 'pending':
                    previous['approval'] = 'superseded'
                    self._put(sid,previous)
                    self._audit(sid, previous['id'], dict(decision='superseded', actor=actor, timestamp=timestamp, result='superseded', message='A new proposal batch replaced this pending proposal.'))
            for s in suggestions:
                current = next(a for a in activities if a['id'] == s['activity_id'])
                item = {**s, 'id':secrets.token_urlsafe(18), 'current':deepcopy(current), 'source_version':current['version'], 'approval':'pending', 'decision_state':'pending', 'calendar_update_state':'not-requested'}
                self.db.execute('INSERT INTO proposals VALUES (?,?,?)', (sid,item['id'],json.dumps(item)))
                saved.append(item)
        return saved

    def _put(self, sid, proposal):
        self.db.execute('UPDATE proposals SET data=? WHERE session=? AND id=?', (json.dumps(proposal),sid,proposal['id']))

    def _audit(self, sid, pid, result):
        self.db.execute('INSERT INTO approval_audit(session,proposal,data) VALUES (?,?,?)', (sid,pid,json.dumps(result)))

    def audit(self, sid):
        return [dict(proposal_id=pid, **json.loads(data)) for pid,data in self.db.execute('SELECT proposal,data FROM approval_audit WHERE session=? ORDER BY id', (sid,))]

    def apply_event(self, sid, proposal):
        """Compare-and-swap source version; notes and unrelated fields are preserved."""
        event = next(a for a in self.events(sid) if a['id'] == proposal['activity_id'])
        event.update(start=proposal['start'],end=proposal['end'])
        cursor = self.db.execute('UPDATE demo_events SET data=?,version=version+1 WHERE session=? AND id=? AND version=?',
                                 (json.dumps(event),sid,event['id'],proposal['source_version']))
        if cursor.rowcount != 1:
            raise ValueError('Source event version changed; request revision')

    def decide(self, sid, proposal, decision, actor, timestamp, checks, reason='', revalidate=None):
        if decision not in ('approve','reject','revise') or not actor or not timestamp:
            raise ValueError('A valid explicit decision, actor and timestamp are required')
        result = dict(decision=decision, actor=actor, timestamp=timestamp, checks=checks,
                      result='rejected' if decision == 'reject' else 'revision-requested',
                      message=reason or 'No calendar times changed.', integration='isolated-demo-calendar')
        with self.db:
            # Reload under a write transaction: never trust a caller's old proposal snapshot.
            self.db.execute('BEGIN IMMEDIATE')
            stored = self.get(sid,proposal['id'])
            if not stored:
                raise ValueError('Proposal not found')
            if stored.get('outcome'):
                if stored['outcome']['decision'] == decision:
                    return stored['outcome']
                raise ValueError('Proposal already decided')
            if stored['approval'] != 'pending':
                raise ValueError('Only a pending proposal can be decided')
            proposal = stored
            if decision == 'approve' and revalidate is not None:
                validation = revalidate()
                checks = validation['checks']
                result['checks'] = checks
                result['policy_validation'] = validation.get('policy_validation')
            proposal['decision_state'] = {'approve':'approved','reject':'rejected','revise':'revision-requested'}[decision]
            proposal['calendar_update_state'] = 'not-requested'
            if decision == 'approve':
                self._audit(sid,proposal['id'],dict(result, result='approved',
                    message='Supervisor approved the proposal; calendar update not yet confirmed.'))
                self._put(sid,proposal)
                result.update(result='blocked', message='Revalidation failed; no calendar times changed.')
                required={'source_version','weather_policy','availability','duration','session_window'}
                if required.issubset(checks) and all(value is True for value in checks.values()):
                    # A savepoint also rolls back partially failed integration writes.
                    self.db.execute('SAVEPOINT calendar_write')
                    try:
                        self.apply_event(sid,proposal)
                        self.db.execute('RELEASE calendar_write')
                        result.update(result='applied', message='Updated the isolated demo calendar. No external calendar was changed.')
                    except Exception:
                        self.db.execute('ROLLBACK TO calendar_write')
                        self.db.execute('RELEASE calendar_write')
                        result.update(result='integration-failed', message='Demo calendar write failed; no changes committed. Request a new proposal.')
            if decision == 'approve':
                proposal['calendar_update_state'] = 'applied' if result['result']=='applied' else 'failed'
            result.update(decision_state=proposal['decision_state'],calendar_update_state=proposal['calendar_update_state'])
            proposal['approval'] = result['result']
            proposal['outcome'] = result
            self._put(sid,proposal)
            self._audit(sid,proposal['id'],result)
        return result

    def annotate(self, sid, event, notes):
        """Narrow note-only CAS write. Time/attendees are never changed here."""
        if event.get('notes','') == notes:
            return 'unchanged'
        with self.db:
            latest = next(a for a in self.events(sid) if a['id']==event['id'])
            latest['notes'] = notes
            cursor = self.db.execute('UPDATE demo_events SET data=?,version=version+1 WHERE session=? AND id=? AND version=?',
                                     (json.dumps(latest),sid,event['id'],event['version']))
            if cursor.rowcount != 1:
                raise ValueError('Event version changed during annotation')
        return 'updated'
