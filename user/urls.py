from django.urls import path, re_path
from . import views


urlpatterns = [
    #用户相关
    re_path(r'^login/$', views.UserLogin.as_view(), name='user-login'),

    re_path(r'^modify/mobile/$', views.UserWxMobileModify.as_view(), name='user-modify-mobile'),
    re_path(r'^(?P<pk>[0-9]+)/$', views.UserDetail.as_view(), name='users-detail'),
    re_path(r'^currentUser/$', views.UserCurrentDetail.as_view(), name='user-detail-current'),

    re_path(r'^feedback/$', views.FeedbackPost.as_view(), name='user-feedback-post'),
    re_path(r'^qa/list/$', views.QAList.as_view(), name='user-qa-list'),
 
    # 用户搜索
    path('search/', views.UserSearchView.as_view(), name='user-search'),
    
    # 积分排行
    path('credit/ranking/', views.UserCreditRankingList.as_view(), name='user-credit-ranking'),

    # 关注列表
    path('follow/list/', views.FollowListView.as_view(), name='follow-list'),
    # 粉丝列表
    path('fans/list/', views.FansListView.as_view(), name='fans-list'),
    # 关注/取消关注
    path('follow/<int:user_id>/', views.FollowView.as_view(), name='follow'),
    
    # 账户余额
    path('balance/', views.UserBalanceView.as_view(), name='user-balance'),
    # 钱包流水
    path('moneylog/list/', views.MoneyLogListview.as_view(), name='user-moneylog'),
    # 提现
    path('withdraw/', views.WithdrawLogView.as_view(), name='user-withdraw'),
    # 积分余额
    path('credit/balance/', views.CreditBalanceView.as_view(), name='user-credit-balance'),
    # 积分明细
    path('creditlog/list/', views.CreditLogListview.as_view(), name='user-creditlog'),
    
    # 我的提问
    path('topic/list/', views.UserTopicListView.as_view(), name='user-topic-list'),
    # 我的回答
    path('topic/reply/list/', views.UserTopicReplyListView.as_view(), name='user-topic-reply-list'),
    # 我的视频
    path('knowledge/list/', views.UserKnowledgeListView.as_view(), name='user-knowledge-list'),

    # 行业列表
    path('profession/list/', views.ProfessionListView.as_view(), name='profession-list'),
    # 专业列表
    path('major/list/', views.MajorListView.as_view(), name='major-list'),
    # 提交认证申请
    path('audit/', views.UserAuditView.as_view(), name='user-audit'),
    # 修改认证申请
    path('audit/<int:pk>/', views.UserAuditUpdateView.as_view(), name='user-audit-detail'),
    
    # 获取/修改专家信息
    path('expert/', views.ExpertView.as_view(), name='expert-info'),
    # 获取专家信息
    path('expert/<int:pk>/', views.ExpertDetailView.as_view(), name='expert-detail'),
    # 专家列表
    path('expert/list/', views.ExpertListView.as_view(), name='expert'),
    # 专家的评论列表
    path('expert/<int:expert_id>/review/list/', views.ExpertReviewListView.as_view(), name='expert-review'),
]

app_name = 'user'
