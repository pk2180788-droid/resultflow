from django.db import migrations

def fill_profiles(apps,schema_editor):
 User=apps.get_model('auth','User'); Profile=apps.get_model('core','Profile')
 for u in User.objects.all(): Profile.objects.get_or_create(user_id=u.pk,defaults={'role':'admin' if u.is_superuser else 'student'})
class Migration(migrations.Migration):
 dependencies=[('core','0002_teacherassignment')]
 operations=[migrations.RunPython(fill_profiles,migrations.RunPython.noop)]
