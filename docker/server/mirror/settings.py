"""Bounded display preferences; never accepts JS, HTML, commands, paths or URLs."""
import copy
WIDGETS=('clock','weather','reminders','calendar','goals','history','news')
SHORTCUTS=('opengym','mealie','javis','reminders','calendar','manyfold','actual','monitor')
DEFAULTS={'widgets':{k:True for k in WIDGETS},'order':list(WIDGETS),'shortcuts':{k:True for k in SHORTCUTS},'clock24':True,'temperatureUnit':'C','backgroundDim':35,'panelOpacity':40,'blur':9,'fontScale':100,'refreshMinutes':5,'newsCount':5}

def defaults():return copy.deepcopy(DEFAULTS)
def validate(value):
 if not isinstance(value,dict) or set(value)!=set(DEFAULTS):raise ValueError('Configuração inválida.')
 for name,keys in (('widgets',WIDGETS),('shortcuts',SHORTCUTS)):
  if not isinstance(value[name],dict) or set(value[name])!=set(keys) or any(type(v)!=bool for v in value[name].values()):raise ValueError('Seleção inválida.')
 if not any(value['widgets'].values()):raise ValueError('Mantenha pelo menos um bloco visível.')
 if not isinstance(value['order'],list) or len(value['order'])!=len(WIDGETS) or any(type(x)!=str for x in value['order']) or set(value['order'])!=set(WIDGETS):raise ValueError('Ordem dos blocos inválida.')
 if type(value['clock24'])!=bool or value['temperatureUnit'] not in ('C','F'):raise ValueError('Formato inválido.')
 for name,low,high in (('backgroundDim',15,85),('panelOpacity',20,85),('blur',0,16),('fontScale',80,125),('refreshMinutes',5,60),('newsCount',1,8)):
  if type(value[name])!=int or not low<=value[name]<=high:raise ValueError('Valor fora do intervalo permitido.')
 return copy.deepcopy(value)
