import os
import django
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from incubator.models import RLTemplate
rl_templates_db = RLTemplate.objects.all().prefetch_related('levels').order_by('id')
rl_data = {}
for rlt in rl_templates_db:
    rl_data[rlt.name] = {}
    for lvl in rlt.levels.all():
        rl_data[rlt.name][str(lvl.level)] = {
            'description': lvl.description
        }

with open("test_out.json", "w") as f:
    f.write(json.dumps(rl_data))

with open("test_out2.js", "w") as f:
    f.write(f"const RL_DATA = {json.dumps(rl_data)};")
