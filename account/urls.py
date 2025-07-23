from django.urls import path
from .views import UserRegisterView, UserLoginView, UserLogoutView, profile_view
from .views import signup_view




urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('signup/', signup_view, name='signup'),

]
