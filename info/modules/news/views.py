from flask import current_app, jsonify, abort, render_template, session, g, request

from info.common import user_loggin_data
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map

# 新闻详情
@news_blu.route('/<int:news_id>')
@user_loggin_data
def news_detail(news_id):  # 全局刷新,后端渲染,返回html

    news = None   # type:News
    # 从数据库取出新闻数据
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return abort(404)

    # 新闻的点击量+1
    news.clicks += 1
    # 查询新闻,按照点击量的倒序排序,取前10条
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
    rank_list = [news.to_dict() for news in rank_list]
    # 将用户信息转换为字典
    is_collected = False
    user = g.user
    if user:
        if news in user.collection_news:
            is_collected = True

    user = user.to_dict() if user else None

    return render_template('news/detail.html', news=news.to_dict(), user=user, rank_list=rank_list, is_collected=is_collected)

# 新闻收藏,是局部刷新,所以只能用前端渲染,
# news_id
# action collect/cancel collect
# 请求方式 post
# 返回参数是json


@news_blu.route('/news_collect', methods=['POST'])
@user_loggin_data
def news_collect():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 校验参数
    if not all({news_id, action}):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 转换整型
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据user_id 查询新闻
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])
    # 根据action执行处理,即将user_id和news_id建立获取取消关系
    if action == 'collect':
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)
    # 返回json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

