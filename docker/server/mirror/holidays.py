"""Persistent calendar catalogue, 2026–2030, based on the laws linked below.

Future dates project current permanent legislation, not unpublished annual decrees.
Optional days off (Carnival, bridge days, Christmas Eve) are deliberately excluded.
"""
import datetime as dt

FIRST_YEAR,LAST_YEAR=2026,2030
NATIONAL='https://www.planalto.gov.br/ccivil_03/leis/l0662.htm'
APARECIDA='https://www.planalto.gov.br/ccivil_03/leis/l6802.htm'
CONSCIENCIA='https://www2.camara.leg.br/legin/fed/lei/2023/lei-14759-21-dezembro-2023-795091-publicacaooriginal-170522-pl.html'
STATE='https://www.al.sp.gov.br/repositorio/legislacao/lei/1997/original-lei-9497-05.03.1997.html'
LOCAL='https://www.jacarei.sp.leg.br/geral/lei-organica-do-municipio-de-jacarei-teste/'
REGIONS={'none':(), 'BR':('BR',), 'BR-SP':('BR','SP'), 'BR-SP-JACAREI':('BR','SP','JACAREI')}

def easter(year):
    # Gregorian computus: arithmetic is independent of timezone and network access.
    a=year%19;b=year//100;c=year%100;d=b//4;e=b%4
    f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30
    i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    return dt.date(year,(h+l-7*m+114)//31,(h+l-7*m+114)%31+1)

def catalogue():
    rows=[]
    fixed=[(1,1,'Confraternização Universal','BR',NATIONAL),
      (4,21,'Tiradentes','BR',NATIONAL),(5,1,'Dia do Trabalho','BR',NATIONAL),
      (9,7,'Independência do Brasil','BR',NATIONAL),(10,12,'Nossa Senhora Aparecida','BR',APARECIDA),
      (11,2,'Finados','BR',NATIONAL),(11,15,'Proclamação da República','BR',NATIONAL),
      (11,20,'Dia Nacional de Zumbi e da Consciência Negra','BR',CONSCIENCIA),
      (12,25,'Natal','BR',NATIONAL),(7,9,'Revolução Constitucionalista','SP',STATE),
      (4,3,'Aniversário de Jacareí','JACAREI',LOCAL),(12,8,'Padroeira de Jacareí','JACAREI',LOCAL)]
    for year in range(FIRST_YEAR,LAST_YEAR+1):
        events=[(dt.date(year,m,d),title,scope,source) for m,d,title,scope,source in fixed]
        events.extend([(easter(year)-dt.timedelta(days=2),'Sexta-feira Santa','JACAREI',LOCAL),
                       (easter(year)+dt.timedelta(days=60),'Corpus Christi','JACAREI',LOCAL)])
        for index,(day,title,scope,source) in enumerate(events):
            rows.append({'id':f'holiday-{year}-{index:02}', 'day':day.isoformat(),
                         'title':title,'scope':scope,'source':source})
    return sorted(rows,key=lambda row:(row['day'],row['id']))
