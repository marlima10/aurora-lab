from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
assert connection.settings_dict['NAME'] == 'wger_test', 'Only the evaluation database is allowed.'
User = get_user_model()
user, _ = User.objects.get_or_create(username='rafael', defaults={'email':'rafael@wger.test','first_name':'Rafael'})
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_unusable_password()
user.save()
for other in User.objects.exclude(pk=user.pk):
    other.is_active=False
    other.set_unusable_password()
    other.save(update_fields=['is_active','password'])
profile=user.userprofile
if hasattr(profile,'time_zone'):
    profile.time_zone='America/Sao_Paulo'
    profile.save(update_fields=['time_zone'])
print('Perfil privado de avaliação preparado; senhas locais desativadas.')
