import random
from django.views.decorators.csrf import csrf_exempt
import builtins  # 加在文件顶部或函数内
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Player, PlayerAttributes
from django.db.models import F
import random

@csrf_exempt
def guess_player_view(request):
    context = {}

    if request.method == 'POST':
        selected = request.POST.get('selected')
        correct = request.POST.get('correct')
        context['answered'] = True
        context['is_correct'] = (selected == correct)

    # 只选出有属性的球员
    selected_attr = PlayerAttributes.objects.select_related(None)\
        .order_by('?')\
        .values(
            'player_fifa_api_id', 'overall_rating', 'potential',
            'preferred_foot', 'attacking_work_rate', 'defensive_work_rate'
        ).first()

    # 直接获取 player 信息
    player = Player.objects.filter(player_fifa_api_id=selected_attr['player_fifa_api_id'])\
        .values('player_name', 'birthday', 'height', 'weight')\
        .first()

    if not player:
        context['error'] = "无法找到对应球员"
        return render(request, 'guess_player.html', context)

    # 构建信息
    attribute_info = {
        key: selected_attr[key] for key in [
            'overall_rating', 'potential', 'preferred_foot',
            'attacking_work_rate', 'defensive_work_rate'
        ]
    }
    attribute_info.update({
        'birthday': player['birthday'],
        'height': player['height'],
        'weight': player['weight']
    })

    # 获取选项
    correct_name = player['player_name']
    other_names = list(
        Player.objects.exclude(player_name=correct_name)
        .values_list('player_name', flat=True)
        .distinct()[:50]  # 限制范围加速
    )
    options = random.sample(other_names, min(3, len(other_names))) + [correct_name]
    random.shuffle(options)

    context.update({
        'attribute_info': attribute_info,
        'options': options,
        'correct': correct_name,
    })

    return render(request, 'guess_player.html', context)

from django.db.models import Avg, Max

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import login
from django.db.models import Q

from .models import (
    UserAccountUser, ManagerAccountUser, League, Team, Player,
    Subscribe, Follow, Match, TeamAttributes, PlayerAttributes, User, FootballManager
)


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'manager_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.db.models import Max
from .models import User, UserAccountUser, ManagerAccountUser, FootballManager

@csrf_exempt
def custom_login_view(request):
    if request.method == 'GET':
        # 清除可能存在的错误 session 数据
        if 'manager_id' in request.session:
            del request.session['manager_id']
        if 'user_id' in request.session:
            del request.session['user_id']
        return render(request, 'login.html')
    if request.method == 'POST':
        identity = request.POST['identity']  # 'user' or 'manager'
        username = request.POST['username']
        password = request.POST['password']

        if identity == 'user':
            try:
                user = UserAccountUser.objects.get(username=username)
                if user.check_password(password):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['user_id'] = user.id
                    request.session['user_username'] = user.username
                    return render(request, 'success_redirect.html', {'identity': '普通用户'})
            except UserAccountUser.DoesNotExist:
                pass

        elif identity == 'manager':
            try:
                manager = ManagerAccountUser.objects.get(username=username)
                if manager.check_password(password):
                    login(request, manager, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['manager_id'] = manager.id
                    request.session['manager_username'] = manager.username
                    return redirect('manager_dashboard')
            except ManagerAccountUser.DoesNotExist:
                pass

        return HttpResponse("用户名或密码错误")

    return HttpResponse("仅支持 POST 登录")

@csrf_exempt
def register_view(request):

    if request.method == 'GET':
        # 清除可能存在的错误 session 数据
        if 'manager_id' in request.session:
            del request.session['manager_id']
        if 'manager_username' in request.session:
            del request.session['manager_username']
        if 'user_id' in request.session:
            del request.session['user_id']
        return render(request, 'register.html')

    if request.method == 'POST':
        identity = request.POST.get('identity')
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        age = request.POST.get('age')

        if identity == 'user':
            if UserAccountUser.objects.filter(username=username).exists():
                return render(request, 'register.html', {'error': '用户名已存在', 'request': request})

            max_user_id = User.objects.aggregate(max_id=Max('user_id'))['max_id'] or 0
            new_user_id = max_user_id + 1

            User.objects.create(user_id=new_user_id, id=new_user_id, name=name, age=age)
            user = UserAccountUser(user_id=new_user_id, id=new_user_id, username=username)
            user.set_password(password)
            user.save(using='default')
            request.session['user_id'] = user.id
            request.session['user_username'] = user.username
            return render(request, 'success_redirect.html', {'identity': '普通用户'})

        elif identity == 'manager':
            if ManagerAccountUser.objects.filter(username=username).exists():
                return render(request, 'register.html', {'error': '用户名已存在', 'request': request})

            max_licence_id = FootballManager.objects.aggregate(max_id=Max('licence_id'))['max_id'] or 0
            new_licence_id = max_licence_id + 1

            FootballManager.objects.create(licence_id=new_licence_id, id=new_licence_id, name=name, age=age)
            manager = ManagerAccountUser(licence_id=new_licence_id, id=new_licence_id, username=username)
            manager.set_password(password)
            manager.save(using='default')
            request.session['manager_id'] = manager.id
            request.session['manager_username'] = manager.username
            return render(request, 'success_redirect_manager.html', {'identity': '经理账号'})

        return HttpResponse("身份类型无效")
    

def home_view(request):
    return render(request, 'index.html')  # 加载主页模板


def user_dashboard(request):
    return render(request, 'user_dashboard.html')



@csrf_exempt
def follow_team_view(request):
    if request.method == 'GET':
        leagues = League.objects.all()
        league_id = request.GET.get('league_id')
        teams = Team.objects.filter(league_id=league_id) if league_id else None
        return render(request, 'follow_team.html', {'leagues': leagues, 'teams': teams, 'league_id': league_id})

    if request.method == 'POST':
        print("======= DEBUG: 登录信息 =======")
        print("当前用户对象：", request.user)
        print("是否已认证：", request.user.is_authenticated)
        print("request.user.id =", request.user.id)
        print("request.user.username =", request.user.username)
        print("================================")
        user_id = request.user.id
        team_api_id = request.POST.get('team_api_id')
        from .models import Subscribe
        max_id = Subscribe.objects.aggregate(max_id=Max('id'))['max_id'] or 0
        new_id = max_id + 1
        # Use user's id field for user_id
        Subscribe.objects.create(id=new_id, user_id=user_id, team_api_id=team_api_id)
        return render(request, 'success_return.html', {'entity': '球队'})



# 关注球员视图
@csrf_exempt
def follow_player_view(request):
    if request.method == 'GET':
        leagues = League.objects.all()
        league_id = request.GET.get('league_id')
        team_api_id = request.GET.get('team_api_id')

        if league_id and not team_api_id:
            teams = Team.objects.filter(league_id=league_id)
            return render(request, 'follow_player.html', {
                'leagues': leagues,
                'teams': teams,
                'league_id': league_id,
                'players': None  #  确保 players 被定义，即使是 None
            })

        elif league_id and team_api_id:
            teams = Team.objects.filter(league_id=league_id)
            players = Player.objects.filter(team_api_id=team_api_id)
            return render(request, 'follow_player.html', {
                'leagues': leagues,
                'teams': teams,
                'players': players,
                'league_id': league_id,
                'team_api_id': team_api_id
            })

        return render(request, 'follow_player.html', {
            'leagues': leagues,
            'players': None  #  没有选择时，players 也应该传入
        })

    if request.method == 'POST':
        print("======= DEBUG: 登录信息 =======")
        print("当前用户对象：", request.user)
        print("是否已认证：", request.user.is_authenticated)
        print("request.user.id =", request.user.id)
        print("request.user.username =", request.user.username)
        print("================================")
        user_id = request.user.id
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        from .models import Follow
        max_id = Follow.objects.aggregate(max_id=Max('id'))['max_id'] or 0
        new_id = max_id + 1
        # Use user's id field for user_id
        Follow.objects.create(id=new_id, user_id=user_id, player_fifa_api_id=player_fifa_api_id)
        return render(request, 'success_return.html', {'entity': '球员'})


def view_followed_teams(request):
    user_id = request.user.id
    subscriptions = Subscribe.objects.filter(user_id=user_id)
    team_ids = [s.team_api_id for s in subscriptions]
    teams = Team.objects.filter(team_api_id__in=team_ids)

    team_names = {t.team_api_id: t.team_long_name for t in teams}  

    print("======= 查看关注球队 DEBUG =======")
    print("当前用户对象：", request.user)
    print("是否已认证：", request.user.is_authenticated)
    print("request.user.id =", request.user.id)
    print("request.user.username =", request.user.username)
    print("==================================")

    from .models import TeamAttributes
    attributes = TeamAttributes.objects.filter(team_api_id__in=team_ids)
    for attr in attributes:
        attr.team_name = team_names.get(attr.team_api_id, '未知球队')

    return render(request, 'view_followed_teams.html', {
        'teams': teams,
        'attributes': attributes,
        'team_names': team_names,  
        'has_data': bool(teams)
    })

def view_followed_players(request):
    user_id = request.user.id
    follows = Follow.objects.filter(user_id=user_id)
    player_ids = [f.player_fifa_api_id for f in follows]
    players = Player.objects.filter(player_fifa_api_id__in=player_ids)

    player_names = {p.player_fifa_api_id: p.player_name for p in players}  

    from .models import PlayerAttributes
    attributes = PlayerAttributes.objects.filter(player_fifa_api_id__in=player_ids)
    for attr in attributes:
        attr.player_name = player_names.get(attr.player_fifa_api_id, '未知球员')
    return render(request, 'view_followed_players.html', {
        'players': players,
        'attributes': attributes,
        'player_names': player_names,  
        'has_data': bool(players)
    })
from django.db.models import Q

def view_followed_matches(request):
    user_id = request.user.id
    team_ids = list(Subscribe.objects.filter(user_id=user_id).values_list('team_api_id', flat=True))
    selected_team_id = request.GET.get('team_id')

    from .models import Match
    from .models import Team

    teams = Team.objects.filter(team_api_id__in=team_ids)

    if selected_team_id:
        matches = Match.objects.filter(
            Q(home_team_api_id=selected_team_id) | Q(away_team_api_id=selected_team_id)
        )
    else:
        matches = Match.objects.filter(
            Q(home_team_api_id__in=team_ids) | Q(away_team_api_id__in=team_ids)
        )

    return render(request, 'view_followed_matches.html', {
        'matches': matches,
        'teams': teams,
        'selected_team_id': selected_team_id,
        'has_data': matches.exists()
    })

@csrf_exempt
def unfollow_team_view(request):
    if request.method == 'GET':
        user_id = request.user.id
        subscriptions = Subscribe.objects.filter(user_id=user_id)
        teams = Team.objects.filter(team_api_id__in=[s.team_api_id for s in subscriptions])
        return render(request, 'unfollow_team.html', {'teams': teams})

    if request.method == 'POST':
        user_id = request.user.id
        team_api_id = request.POST.get('team_api_id')
        Subscribe.objects.filter(user_id=user_id, team_api_id=team_api_id).delete()
        return render(request, 'success_return.html', {'entity': '取消关注的球队'})


@csrf_exempt
def unfollow_player_view(request):
    if request.method == 'GET':
        user_id = request.user.id
        follows = Follow.objects.filter(user_id=user_id)
        players = Player.objects.filter(player_fifa_api_id__in=[f.player_fifa_api_id for f in follows])
        return render(request, 'unfollow_player.html', {'players': players})

    if request.method == 'POST':
        user_id = request.user.id
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        Follow.objects.filter(user_id=user_id, player_fifa_api_id=player_fifa_api_id).delete()
        return render(request, 'success_return.html', {'entity': '取消关注的球员'})
    
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Subscribe, Team, TeamAttributes
import math

@csrf_exempt
def recommend_team_view(request):
    user_id = request.user.id
    if request.method == 'POST':
        team_api_id = request.POST.get('team_api_id')
        if team_api_id:
            # 生成唯一 id（你也可以用 max+1 替代）
            next_id = (Subscribe.objects.aggregate(Max('id'))['id__max'] or 0) + 1
            Subscribe.objects.create(
                id=next_id,
                user_id=user_id,
                team_api_id=team_api_id
            )

            return redirect('/recommend_team/')
    subscriptions = Subscribe.objects.filter(user_id=user_id)
    followed_team_ids = [s.team_api_id for s in subscriptions]

    # 可选的球队属性字段
    attribute_fields = [
        'buildupplayspeed', 'buildupplaypassing', 'chancecreationpassing',
        'chancecreationshooting', 'defencepressure', 'defenceaggression',
        'defenceteamwidth'
    ]

    # 获取已关注球队的属性
    followed_attrs = TeamAttributes.objects.filter(team_api_id__in=followed_team_ids)

    # 工具函数：获取属性向量
    def get_vector(obj):
        return [builtins.getattr(obj, field, 0) for field in attribute_fields]

    if not followed_attrs:
        return render(request, 'recommend_team.html', {
            'message': '您还没有关注任何球队，无法进行推荐。',
            'recommended_teams': [],
            'recommended_attrs': []
        })

    # 计算平均向量
    avg_vector = [0] * len(attribute_fields)
    for attr in followed_attrs:
        vec = get_vector(attr)
        avg_vector = [a + b for a, b in zip(avg_vector, vec)]
    avg_vector = [v / len(followed_attrs) for v in avg_vector]

    # 候选球队（未关注）
    candidate_attrs = TeamAttributes.objects.exclude(team_api_id__in=followed_team_ids)

    # 欧几里得距离
    def euclidean_distance(vec1, vec2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    # 排序推荐
    scored = []
    for attr in candidate_attrs:
        vec = get_vector(attr)
        if all(x is not None for x in vec):
            distance = euclidean_distance(avg_vector, vec)
            scored.append((distance, attr))

    scored.sort(key=lambda x: x[0])
    top_attrs = [item[1] for item in scored[:10]]
    team_ids = [a.team_api_id for a in top_attrs]
    teams = Team.objects.filter(team_api_id__in=team_ids)

    return render(request, 'recommend_team.html', {
        'recommended_attrs': top_attrs,
        'recommended_teams': teams,
        'message': None
    })

from django.contrib.auth import logout
from django.shortcuts import redirect
def logout_view(request):
    logout(request)
    return redirect('custom_login')


#########
def manager_dashboard(request):
    return render(request, 'manager_dashboard.html')


# =========================
# Manager functionality: add/view/remove interested players
# =========================
# 处理经理关注球员的视图函数
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from.models import FootballManager, Interested, Player

@manager_required
def manager_follow_player_view(request):
    manager_id = request.session.get('manager_id')
    football_manager = get_object_or_404(FootballManager, id=manager_id)
    
    if request.method == 'GET':
        leagues = League.objects.all()
        league_id = request.GET.get('league_id')
        team_api_id = request.GET.get('team_api_id')

        if league_id and not team_api_id:
            teams = Team.objects.filter(league_id=league_id)
            return render(request, 'manager_follow_player.html', {
                'leagues': leagues,
                'teams': teams,
                'league_id': league_id,
                'players': None
            })

        elif league_id and team_api_id:
            teams = Team.objects.filter(league_id=league_id)
            players = Player.objects.filter(team_api_id=team_api_id)
            return render(request, 'manager_follow_player.html', {
                'leagues': leagues,
                'teams': teams,
                'players': players,
                'league_id': league_id,
                'team_api_id': team_api_id
            })

        return render(request, 'manager_follow_player.html', {
            'leagues': leagues,
            'players': None
        })

    if request.method == 'POST':
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        
        if player_fifa_api_id:
            if not Interested.objects.filter(
                manager=football_manager,
                player_fifa_api_id=player_fifa_api_id
            ).exists():
                Interested.objects.create(
                    manager=football_manager,
                    player_fifa_api_id=player_fifa_api_id
                )
            return redirect('manager_view_interested_players')
        else:
            return redirect('manager_follow_player')

@manager_required
def manager_view_interested_players(request):
    manager_id = request.session.get('manager_id')
    football_manager = get_object_or_404(FootballManager, id=manager_id)
    
    interest_records = Interested.objects.filter(manager=football_manager)
    player_fifa_ids = [record.player_fifa_api_id for record in interest_records]
    
    interested_players = Player.objects.filter(
        player_fifa_api_id__in=player_fifa_ids
    )
    
    context = {
        'interested_players': interested_players,
        'manager': football_manager
    }
    return render(request, 'manager_view_interested_players.html', context)


# 查询雇佣关系
# soccer_project/soccer_app/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Employ, Team, League, TeamAttributes

def check_employment(request):
    manager_id = request.session.get('manager_id')
    if not manager_id:
        return redirect('login')  # 未登录，重定向到登录页
    
    # 打印当前经理人ID用于调试
    print(f"当前经理人ID: {manager_id}")

    # 查询当前经理人是否有雇佣关系
    employment = Employ.objects.filter(id=manager_id).first()

    if employment:
        team = Team.objects.get(team_api_id=employment.team_api_id)
        return render(request, 'manager_check_employment.html', {
            'has_employment': True,
            'team': team
        })

    # 获取联赛 ID
    league_id = request.GET.get('league_id')

    # 处理选择球队请求
    if request.method == 'POST':
        team_api_id = request.POST.get('team_api_id')
        if not team_api_id:
            messages.error(request, 'Please select a team')
            return redirect('manager_check_employment')

        # 验证是否已有雇佣关系
        if Employ.objects.filter(id=manager_id).exists():
            messages.error(request, 'You can only manage one club at a time')
            return redirect('manager_check_employment')

        try:
            # 创建雇佣关系
            Employ.objects.create(id=manager_id, team_api_id=team_api_id)
            return redirect('manager_application_success')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('manager_check_employment')

    # 获取所有联赛
    leagues = League.objects.all()

    # 根据联赛 ID 筛选球队
    teams = []
    show_teams = False
    if league_id:
        teams = Team.objects.filter(league_id=league_id)
        show_teams = True

    return render(request, 'manager_check_employment.html', {
        'has_employment': False,
        'leagues': leagues,
        'teams': teams,
        'show_teams': show_teams,
        'league_id': league_id
    })

#经理人查看我的球队
from django.shortcuts import render
from .models import Employ, Team, TeamAttributes, Player, PlayerAttributes

def view_my_team(request):
    manager_id = request.user.id
    employment = Employ.objects.filter(id=manager_id).first()

    if not employment:
        return render(request, 'manager_view_my_team.html', {
            'has_team': False
        })

    # 获取球队信息
    try:
        team = Team.objects.get(team_api_id=employment.team_api_id)
    except Team.DoesNotExist:
        team = None

    # 获取球队最新属性
    team_attr = TeamAttributes.objects.filter(
        team_api_id=employment.team_api_id
    ).order_by('-date').first()

    # 获取球队球员及其最新属性
    players_with_attrs = []
    for player in Player.objects.filter(team_api_id=employment.team_api_id):
        # 获取每个球员的最新属性
        attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id=player.player_fifa_api_id
        ).order_by('-date').first()
        
        players_with_attrs.append({
            'player': player,
            'attributes': attrs
        })

    return render(request, 'manager_view_my_team.html', {
        'has_team': True,
        'team': team,
        'team_attr': team_attr,
        'players_with_attrs': players_with_attrs
    })

#经理人查看我的球员
# 查看我的球队球员列表
def manager_view_my_players(request):
    manager_id = request.user.id
    employment = Employ.objects.filter(id=manager_id).first()

    if not employment:
        return render(request, 'manager_view_my_players.html', {
            'has_team': False
        })

    # 获取球队球员
    players = Player.objects.filter(team_api_id=employment.team_api_id)

    return render(request, 'manager_view_my_players.html', {
        'has_team': True,
        'players': players
    })

# 经理人再查看我的队里的球员数值
# 查看球员详细信息
def manager_view_player_details(request, player_fifa_api_id):
    try:
        player = Player.objects.get(player_fifa_api_id=player_fifa_api_id)
        attributes = PlayerAttributes.objects.filter(player_fifa_api_id=player_fifa_api_id).first()
        return render(request, 'manager_view_player_details.html', {'player': player, 'attributes': attributes})
    except Player.DoesNotExist:
        # 处理球员不存在的情况
        return render(request, 'error_page.html', {'error_message': '未找到该球员信息'})

#申请成功视图
from django.shortcuts import render
def application_success(request):
    return render(request, 'application_success.html')

#查看所有球员和他们的数值
def manager_view_all_players(request):
    # 获取筛选和搜索参数
    league_id = request.GET.get('league_id')
    team_api_id = request.GET.get('team_api_id')
    search_query = request.GET.get('search_query')
    
    # 初始查询集
    players = Player.objects.all()
    
    # 应用筛选条件
    if league_id:
        teams_in_league = Team.objects.filter(league_id=league_id)
        team_ids = [team.team_api_id for team in teams_in_league]
        players = players.filter(team_api_id__in=team_ids)
    
    if team_api_id:
        players = players.filter(team_api_id=team_api_id)
    
    # 应用搜索条件
    if search_query:
        players = players.filter(player_name__icontains=search_query)
    
    # 获取所有联赛和球队，用于筛选下拉框
    leagues = League.objects.all()
    teams = Team.objects.all()
    
    return render(request, 'manager_view_all_players.html', {
        'players': players,
        'leagues': leagues,
        'teams': teams,
        'selected_league_id': league_id,
        'selected_team_api_id': team_api_id,
        'search_query': search_query
    })

def manager_view_player_attributes(request, player_fifa_api_id):
    player = Player.objects.get(player_fifa_api_id=player_fifa_api_id)
    attributes = PlayerAttributes.objects.filter(player_fifa_api_id=player_fifa_api_id).first()
    return render(request, 'manager_view_player_attributes.html', {'player': player, 'attributes': attributes})

#经理删除感兴趣球员
@csrf_exempt
@manager_required
def manager_delete_interested_player(request, player_fifa_api_id):
    manager_id = request.session.get('manager_id')
    football_manager = get_object_or_404(FootballManager, id=manager_id)
    
    Interested.objects.filter(
        manager=football_manager,
        player_fifa_api_id=player_fifa_api_id
    ).delete()
    
    return redirect('manager_view_interested_players')


def delete_success(request):
    return render(request, 'delete_success.html')


from django import template
register = template.Library()

@register.filter
def getattr(obj, attr):
    return getattr(obj, attr, '')


#添加推荐球员
@csrf_exempt
def recommend_player_view(request):
    manager_id = request.user.id  # 当前经理的ID

    # 定义可用于推荐的球员属性列表
    all_attributes = [
        'overall_rating', 'potential', 'crossing', 'finishing', 'heading_accuracy',
        'short_passing', 'volleys', 'dribbling', 'curve', 'free_kick_accuracy',
        'long_passing', 'ball_control', 'acceleration', 'sprint_speed', 'agility',
        'reactions', 'balance', 'shot_power', 'jumping', 'stamina', 'strength',
        'long_shots', 'aggression', 'interceptions', 'positioning', 'vision',
        'penalties', 'marking', 'standing_tackle', 'sliding_tackle',
    ]

    selected_attribute = request.GET.get('attribute')
    recommended_players = []
    message = ''

    # 获取当前经理感兴趣的球员ID列表
    interested_player_ids = Interested.objects.filter(
        manager_id=manager_id
    ).values_list('player_fifa_api_id', flat=True)

    if selected_attribute:
        # 计算感兴趣球员的选定属性平均值
        followed_attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id__in=interested_player_ids
        ).exclude(**{selected_attribute: None})

        valid_values = []
        for attr in followed_attrs:
            try:
                value = int(getattr(attr, selected_attribute))
                valid_values.append(value)
            except (ValueError, TypeError):
                continue

        if valid_values:
            avg_value = sum(valid_values) / len(valid_values)
            
            # 查找与平均值相近的球员（排除已感兴趣的）
            recommended_attrs = PlayerAttributes.objects.filter(
                **{f"{selected_attribute}__gte": avg_value - 5, f"{selected_attribute}__lte": avg_value + 5}
            ).exclude(player_fifa_api_id__in=interested_player_ids)

            # 获取推荐球员的详细信息，并添加属性值到上下文
            recommended_players = []
            for attr in recommended_attrs:
                try:
                    player = Player.objects.get(player_fifa_api_id=attr.player_fifa_api_id)
                    recommended_players.append({
                        'player': player,
                        'attribute_value': getattr(attr, selected_attribute),
                    })
                except Player.DoesNotExist:
                    continue

            if not recommended_players:
                message = "没有找到符合条件的推荐球员"
        else:
            message = "您感兴趣的球员中没有有效的该属性数据"

    if request.method == 'POST':
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        if player_fifa_api_id:
            # 使用 player_fifa_api_id 添加感兴趣的球员
            Interested.objects.create(
                manager_id=manager_id,
                player_fifa_api_id=player_fifa_api_id
            )
            return redirect('manager_view_interested_players')

    return render(request, 'recommend_player.html', {
        'attributes': all_attributes,
        'selected_attribute': selected_attribute,
        'recommended_players': recommended_players,
        'message': message,
    })