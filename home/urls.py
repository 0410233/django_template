from django.urls import path
from . import views

urlpatterns = [
    # 搜索
    path('search/', views.SearchView.as_view(), name='search'),
    # 首页轮播图
    path('carousel/', views.HomeCarouselView.as_view(), name='home-carousel'),
    # 热门专家
    path('expert/hot/', views.HotExpertList.as_view(), name='home-hot-expert'),
    # 推荐视频
    path('knowledge/recommend/', views.RecommendKnowledgeList.as_view(), name='home-recommend-knowledge'),
]

app_name = 'home'
