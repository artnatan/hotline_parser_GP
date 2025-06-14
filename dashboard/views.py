# Copyright 2025 Calabaraburus (Artem Natalchishin)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.shortcuts import render
from scraper.models import Product

RRP = {
    "Nova Tec NT-S 50": 3699,
    "Nova Tec NT-S 80": 4245,
    "Nova Tec NT-S 100": 4888
}

def product_table(request):
    data = {}
    for model, rrp in RRP.items():
        offers = Product.objects.filter(name=model)
        data[model] = {
            "rrp": rrp,
            "offers": offers
        }
    return render(request, "dashboard/table.html", {"data": data})

