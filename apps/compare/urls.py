from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('compare-excel-to-excel/', views.compare_exceltoexcel, name='compare_excel_excel'),
    path('excel-to-api/', views.compare_exceltoapi, name='compare_excel_api'),
]