from django.urls import path
from . import views

urlpatterns = [
    # 文章详情
    path('<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
]

app_name = 'article'
