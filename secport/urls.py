from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('privacy', views.privacy, name='privacy'),
	path('dashboard', views.dashboard, name='dashboard'),
	path('prelinks/<str:group>/', views.prelinks, name='prelinks'),
    path('<str:group>/', views.submission, name='submission'),
    path('<str:group>/<str:parent_num>/', views.submission, name='comment')
]
