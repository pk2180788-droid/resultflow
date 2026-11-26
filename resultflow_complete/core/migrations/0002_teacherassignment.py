from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
 dependencies=[('core','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
 operations=[migrations.CreateModel(name='TeacherAssignment',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('class_name',models.CharField(blank=True,max_length=60)),('subject',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='core.subject')),('teacher',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='subject_assignments',to=settings.AUTH_USER_MODEL))]),migrations.AlterUniqueTogether(name='teacherassignment',unique_together={('teacher','subject','class_name')})]
