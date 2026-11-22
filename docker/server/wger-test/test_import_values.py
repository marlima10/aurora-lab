import unittest
from decimal import Decimal
from import_values import map_set
class ImportValuesTest(unittest.TestCase):
 def test_cardio_keeps_minutes_and_speed(self):
  self.assertEqual(map_set({'min':1.25,'speed':8.4}), (Decimal('1.25'),'Minutes',Decimal('8.4'),'Kilometers Per Hour'))
 def test_strength_preserves_fractional_weight(self):
  self.assertEqual(map_set({'r':12,'w':2.5}), (Decimal('12'),'Repetitions',Decimal('2.5'),None))
 def test_absent_values_are_not_zero_measurements(self):
  self.assertEqual(map_set({}), (None,'Repetitions',None,None))
if __name__=='__main__':unittest.main()
