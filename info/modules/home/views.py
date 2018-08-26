from flask import render_template, current_app, session, request, jsonify

from info.constants import CLICK_RANK_MAX_NEWS, HOME_PAGE_MAX_NEWS
from info.models import User, News, Category
from info.utils.response_code import RET, error_map
from . import home_blu


# 2.蓝图对象管理视图函数
@home_blu.route('/')
def index():
    # 判断用户是否进行过登录
    user_id = session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)
    user = user.to_dict() if user else None

    # 查询新闻,按照点击量的倒序排序,取前10条
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
    rank_list = [news.to_dict() for news in rank_list]

    # 查询所有的分类
    categories = list()
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
    # 在模板中进行替换
    return render_template('news/index.html', user=user, rank_list=rank_list, categories=categories)


@home_blu.route('/favicon.ico')  # favicon.ico图标
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@home_blu.route('/get_news_list')
def get_news_list():
    # 获取参数
    cid = request.args.get('cid')
    cur_page = request.args.get('cur_page')
    per_count = request.args.get('per_count', HOME_PAGE_MAX_NEWS)
    # 校验参数
    if not all([cid, cur_page]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 将参数转化为整形
    try:
        cid = int(cid)
        per_count = int(per_count)
        cur_page = int(cur_page)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    filter_list = list()
    if cid != 1:
        filter_list.append(News.category_id == cid)
    # 根据参数查询新闻数据 按照分类进行分页查询(生成日期倒序)
    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cur_page, per_count)
    except BaseException as e:
        current_app.loggger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    data = {
        'news_list': [news.to_dict() for news in pn.items],
        'total_page': pn.pages
    }

    # 将数据以json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=data)

