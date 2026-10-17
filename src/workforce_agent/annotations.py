"""Product-owned informational disclaimer rendering, independent of rescheduling."""
import re

START = '[CLIMATE WORKFORCE NOTICE]'
END = '[/CLIMATE WORKFORCE NOTICE]'


def annotate_notes(notes: str, warnings: list[dict]) -> str:
    notice = '\n'.join([START, 'INFORMATIONAL DEMO CLIMATE NOTICE — not safety clearance.',
        *[f"{w['severity']} {w['title']}: {w['start']} to {w['end']}; {w['measure']}; forecast {w['source']}, updated {w['updated_at']}; policy {w['policy']}." for w in warnings],
        'Follow configured site policy and official safety procedures.', END])
    pattern = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)
    if START in notes or END in notes:
        if notes.count(START) != 1 or notes.count(END) != 1 or not pattern.search(notes):
            raise ValueError('Malformed product-owned note section; manual review required')
        return pattern.sub(lambda _: notice, notes, count=1)
    return notes + ('\n\n' if notes else '') + notice
