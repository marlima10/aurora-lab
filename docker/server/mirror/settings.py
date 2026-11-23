"""Bounded display preferences; no JS, commands, filesystem paths or arbitrary URLs."""
import copy
import math
from holidays import REGIONS
WIDGETS=('clock','weather','reminders','calendar','goals','history','news')
SHORTCUTS=('opengym','mealie','javis','reminders','calendar','manyfold','actual','monitor')
DEFAULTS={'widgets':{k:True for k in WIDGETS},'order':list(WIDGETS),'shortcuts':{k:True for k in SHORTCUTS},'clock24':True,'temperatureUnit':'C','backgroundDim':35,'panelOpacity':40,'blur':9,'fontScale':100,'refreshMinutes':5,'newsCount':5,'weatherLocation':None,'calendarView':'month','holidayRegion':'BR'}

def defaults():return copy.deepcopy(DEFAULTS)

def migrate(value):
    # Only stored older records gain new keys. HTTP updates still require a complete schema.
    if not isinstance(value,dict):raise ValueError('Configuração inválida.')
    return validate(defaults()|value)

def validate(value):
    if not isinstance(value,dict) or set(value)!=set(DEFAULTS):raise ValueError('Configuração inválida.')
    for name,keys in (('widgets',WIDGETS),('shortcuts',SHORTCUTS)):
        if not isinstance(value[name],dict) or set(value[name])!=set(keys) or any(type(v)!=bool for v in value[name].values()):raise ValueError('Seleção inválida.')
    if not any(value['widgets'].values()):raise ValueError('Mantenha pelo menos um bloco visível.')
    if not isinstance(value['order'],list) or len(value['order'])!=len(WIDGETS) or any(type(x)!=str for x in value['order']) or set(value['order'])!=set(WIDGETS):raise ValueError('Ordem dos blocos inválida.')
    if type(value['clock24'])!=bool or value['temperatureUnit'] not in ('C','F'):raise ValueError('Formato inválido.')
    for name,low,high in (('backgroundDim',15,85),('panelOpacity',20,85),('blur',0,16),('fontScale',80,125),('refreshMinutes',5,60),('newsCount',1,8)):
        if type(value[name])!=int or not low<=value[name]<=high:raise ValueError('Valor fora do intervalo permitido.')
    if value['calendarView'] not in ('month','week') or value['holidayRegion'] not in REGIONS:raise ValueError('Calendário inválido.')
    loc=value['weatherLocation']
    if loc is not None:
        if not isinstance(loc,dict) or set(loc)!={'name','lat','lon'}:raise ValueError('Local inválido.')
        if not isinstance(loc['name'],str) or not 1<=len(loc['name'].strip())<=160 or any(ord(c)<32 for c in loc['name']):raise ValueError('Nome do local inválido.')
        for key,limit in [('lat',90),('lon',180)]:
            if type(loc[key]) not in (int,float) or not math.isfinite(loc[key]) or not -limit<=loc[key]<=limit:raise ValueError('Coordenadas inválidas.')
    return copy.deepcopy(value)
