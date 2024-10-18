from django.urls import path
from .views import *
from django.urls.conf import include


urlpatterns = [
    path('initiate_all/<int:pk>/', initiate_all),
    path('ping/', ping),
    path('register/', register_seller),
    path('get_posts/', get_posts),
    path('get_update/', get_update),
    path('delete_post/<int:pk>/', delete_post),
    path('get_products/', get_products),
    path('create_prod/', create_prod),
    path('get_quest_mod/<int:pk>/', get_quest_mod),
    path('set_quest/<int:pk>/', set_quest),
    path('get_price_per/', get_price_per),
    path('create_campaign/', create_campaign),
    path('get_campaign/<int:pk>/', get_campaign),
    path('set_checked/<str:slug>/', set_checked),
    path('get_prospects/<int:pk>/', get_prospects),
    path('set_resume/<int:pk>/', set_resume),
    path('get_tokens/<int:pk>/', get_tokens),
    path('get_prospect/<int:pk>/', get_prospect),
    path('get_user/', get_user),
    path('get_min_pay/', get_min_pay),
    path('make_payment/', make_payment),
    path('get_pays/', get_pays),
    path('get_my_company/', get_my_company)
]
