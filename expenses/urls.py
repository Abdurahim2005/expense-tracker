from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('categories/', views.category_list_create, name='category_list'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/update/<int:pk>/', views.expense_update, name='expense_update'), 
    path('expenses/delete/<int:pk>/', views.expense_delete, name='expense_delete'),
]