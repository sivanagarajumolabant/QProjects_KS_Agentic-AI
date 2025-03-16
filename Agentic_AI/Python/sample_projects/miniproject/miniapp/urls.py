from django.urls import path
from .views import *


urlpatterns = [
    path('create/', create_emp, name='create_emp'),
    path('list/', emp_list, name='list_emp'),
    path('update/<int:id>/', update_emp, name='update_emp'),
    path('delete/<int:id>/', delete_emp, name='delete_emp')
]
