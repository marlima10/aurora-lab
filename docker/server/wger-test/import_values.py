from decimal import Decimal

def map_set(value):
    if isinstance(value.get('min'), (int,float)):
        return Decimal(str(value['min'])), 'Minutes', Decimal(str(value['speed'])) if isinstance(value.get('speed'),(int,float)) else None, 'Kilometers Per Hour'
    return (Decimal(str(value['r'])) if isinstance(value.get('r'),(int,float)) else None, 'Repetitions', Decimal(str(value['w'])) if isinstance(value.get('w'),(int,float)) else None, None)
